"""
"오늘의 건강 상식" 숏폼 엔드투엔드 파이프라인 — 완전 자동 모드.
대본 생성(Gemini + 검색 그라운딩) → 자동 컴플라이언스 점검 → 음성/자막 생성 → 영상 합성.

사람 검수 없이 매일 자동 실행하는 걸 전제로 설계했다. 대신 아래 두 가지를 기계적으로 강제해서
최소한의 안전장치로 삼는다:
  1. script_prompt.generate_script()가 실제 검색 근거 없이 만들어진 대본을 자동으로 차단한다
     (UnverifiedContentError).
  2. 이 파일의 compliance_check()가 금지 표현/필수 고지 문구를 스캔해서, 위반 시 영상을
     만들지 않고 건너뛴다.
둘 다 통과한 것만 영상으로 만들어진다. 그래도 100% 정확성을 보장하지는 않으므로, 여유가
생기면 output/ 폴더의 metadata.json으로 가끔 스팟체크하는 걸 권장한다.

업로드는 이 스크립트가 자동으로 하지 않는다 — 만들어진 mp4 경로만 반환한다.

실행: python pipeline.py "단백질은 하루에 얼마나 먹어야 할까?" "영양 기초"
"""

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

# Windows 콘솔 기본 코드페이지(cp949)가 이모지(⛔✅)를 못 그려서 print()가 죽는 문제 방지.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPO_ROOT = os.path.dirname(BASE_DIR)
ARTICLES_DIR = os.path.join(REPO_ROOT, "web", "content", "articles")

import topic_calendar
from compose_video import compose_short
from script_prompt import (
    GeneratedScript,
    ScriptRequest,
    UngroundedStatisticError,
    UnverifiedContentError,
    generate_script,
)
from stock_photo import search_photos
from typecast_tts import VOICE_PILJAE, generate_narration_with_words
from pronunciation import apply_pronunciation_fixes, restore_original_spelling

# COMPLIANCE_COPY_GUIDE.md의 금지 표현 목록 — 자동 점검용 (사람 검수 없이 이게 최종 게이트)
BANNED_PATTERNS = [
    "치료합니다", "치료됩니다", "완치", "처방", "주치의", "AI 의사", "AI 주치의",
    "낫습니다", "낫는다", "질병을 예방합니다",
]

REQUIRED_DISCLAIMER = "이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다."
SITE_URL = "https://hankki-nine.vercel.app"


def build_pinned_comment(source: str, next_topic_hint: str, article_url: str | None = None) -> str:
    """업로드 후 등록할 고정 댓글 텍스트를 메타데이터로부터 자동 생성한다 (출처 재확인 +
    웹사이트 링크 + 다음 편 예고 + 소통 유도). upload_and_comment()에 넘겨서 실제로 등록한다."""
    lines = []
    if source:
        lines.append(f"📎 이 영상의 참고 자료: {source}")
    if article_url:
        lines.append(f"📖 이 영상 대본을 글로 다시 보기: {article_url}")
    lines.append(f"🍽️ 내 맞춤 식단 30초 만에 확인: {SITE_URL}")
    lines.append("영상 어떠셨나요? 궁금하신 점이나 다뤄줬으면 하는 주제는 댓글로 남겨주세요!")
    if next_topic_hint:
        lines.append(f"다음 편 예고: '{next_topic_hint}' 다뤄볼게요 🙂")
    lines.append(REQUIRED_DISCLAIMER)
    return "\n\n".join(lines)


KST = timezone(timedelta(hours=9))


def next_publish_time_kst(hour: int = 19, minute: int = 0) -> str:
    """오늘(KST) 지정 시각을 유튜브 scheduled_publish_at 형식으로 반환한다.
    my-video-creator/english_words_short.py의 "익일 07:30 예약" 패턴과 동일한 방식 —
    실행 시각(예: WSL cron이 도는 새벽 5시)과 실제 공개 시각(예: 오후 7시)을 분리해서,
    노트북이 그 공개 시각에 켜져 있지 않아도 유튜브 서버가 알아서 정시에 공개해준다."""
    now = datetime.now(KST)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target.isoformat(timespec="seconds")


def upload_and_comment(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    source: str,
    next_topic_hint: str,
    credentials_file: str = "credentials.json",
    category_id: str = "27",
    final_privacy: str = "public",
    scheduled_publish_at: str | None = None,
    article_url: str | None = None,
) -> dict:
    """댓글까지 단 뒤 최종 공개범위로 전환하는 표준 업로드 절차.

    scheduled_publish_at이 주어지면(예: next_publish_time_kst()) my-video-creator/
    english_words_short.py와 완전히 같은 패턴을 탄다 — youtube_upload.upload_video()가
    privacy_status='public' + scheduled_publish_at + comment_text를 함께 받으면 내부적으로
    ①일부공개(unlisted)로 먼저 올림 → ②댓글 등록 → ③private + 예약 시각으로 전환하고, 그
    시각이 되면 유튜브가 자동으로 공개 전환한다. 이 경로가 표준이고, scheduled_publish_at을
    안 주면(즉시 공개/비공개) 아래의 수동 unlisted→댓글→전환 절차를 대신 쓴다.

    수동 절차가 필요했던 이유: privacy_status='private'로 바로 올린 영상은 commentThreads.insert가
    몇 분~20분 넘게 기다려도 403 Forbidden으로 실패하는 경우가 있었다 (유튜브가 완전 비공개
    영상은 댓글 기능 활성화를 미루는 것으로 추정). 반면 잠깐 unlisted로 올리면 거의 즉시(약 10초)
    댓글이 성공한다."""
    from youtube_upload import get_authenticated_service, insert_comment, upload_video

    comment_text = build_pinned_comment(source, next_topic_hint, article_url)

    if scheduled_publish_at:
        return upload_video(
            file_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status="public",
            credentials_file=credentials_file,
            category_id=category_id,
            scheduled_publish_at=scheduled_publish_at,
            comment_text=comment_text,
        )

    upload_status = "unlisted" if final_privacy == "private" else final_privacy
    result = upload_video(
        file_path=video_path,
        title=title,
        description=description,
        tags=tags,
        privacy_status=upload_status,
        credentials_file=credentials_file,
        category_id=category_id,
    )
    if not result.get("success"):
        return result

    video_id = result["video_id"]
    youtube = get_authenticated_service(credentials_file=credentials_file)
    time.sleep(10)
    comment_id = insert_comment(youtube, video_id, comment_text)

    if final_privacy != upload_status:
        youtube.videos().update(
            part="status", body={"id": video_id, "status": {"privacyStatus": final_privacy}}
        ).execute()

    return {"success": True, "video_id": video_id, "comment_id": comment_id}


def compliance_check(script_text: str) -> list[str]:
    """금지 표현 자동 점검. 위반 목록을 반환 (빈 리스트면 통과)."""
    issues = []
    # 필수 고지 문구 자체에 "처방" 등이 포함되어 있어, 점검 대상에서는 제외하고 검사한다.
    body_text = script_text.replace(REQUIRED_DISCLAIMER, "")
    for pattern in BANNED_PATTERNS:
        if pattern in body_text:
            issues.append(f"금지 표현 포함: '{pattern}'")
    if REQUIRED_DISCLAIMER not in script_text:
        issues.append("필수 고지 문구가 없음")
    return issues


def _save_metadata(path: str, result: GeneratedScript, issues: list[str]) -> None:
    """나중에 스팟체크할 수 있도록 대본/출처/검색 근거를 파일로 남긴다."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(),
                "title": result.title,
                "script": result.script,
                "source": result.source,
                "tags": result.tags,
                "image_query": result.image_query,
                "next_topic_hint": result.next_topic_hint,
                "grounding_sources": result.grounding_sources,
                "compliance_issues": issues,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def slug_from_video_path(video_path: str) -> str:
    """output/{date_tag}_short.mp4 → 웹사이트 아티클 slug(URL에 그대로 씀).
    _publish_article()과 build_description()/build_pinned_comment()가 같은 slug를
    쓰도록 한 곳에 모아둔다."""
    date_tag = os.path.splitext(os.path.basename(video_path))[0].removesuffix("_short")
    return date_tag.replace("_", "-")


def build_description(result: GeneratedScript, article_url: str | None = None) -> str:
    """result.script(고지 문구 포함)+출처+웹사이트 링크+해시태그로 업로드 설명란을 자동 생성한다.
    지금까지 upload_*.py를 만들 때마다 손으로 하던 걸 그대로 코드로 옮긴 것. 실행 설계도
    Phase 3("영상 설명란에 웹사이트 링크")를 여기서 채운다."""
    parts = [result.script]
    if result.source:
        parts.append(f"출처: {result.source}")
    parts.append(f"🍽️ 내 맞춤 식단 30초 만에 확인: {SITE_URL}")
    if article_url:
        parts.append(f"📖 이 영상 대본 전체 읽기: {article_url}")
    hashtags = " ".join(f"#{tag}" for tag in result.tags) + " #한끼정답"
    parts.append(hashtags)
    return "\n\n".join(parts)


def _generate_and_compose(
    topic: str | None, cluster: str | None, voice_id: str
) -> tuple[str | None, GeneratedScript | None, str | None]:
    """대본 생성부터 mp4 합성까지. 차단되거나 캘린더가 비어있으면 (None, None, None)을 반환한다."""
    upcoming_topic = None
    if topic is None:
        today_item, upcoming_item = topic_calendar.pop_next()
        if not today_item:
            print("⛔ 콘텐츠 캘린더 큐가 비어있습니다. 먼저 채워주세요:")
            print("   python topic_calendar.py")
            return None, None, None
        topic = today_item["topic"]
        cluster = today_item["cluster"]
        upcoming_topic = upcoming_item["topic"] if upcoming_item else None
        print(f"📅 캘린더에서 주제를 이어받습니다: [{cluster}] {topic}")
    elif cluster is None:
        raise ValueError("topic을 직접 지정할 때는 cluster도 함께 지정해야 합니다.")

    print(f"대본 생성 중... (주제: {topic})")
    try:
        result = generate_script(ScriptRequest(topic=topic, cluster=cluster, upcoming_topic=upcoming_topic))
    except (UnverifiedContentError, UngroundedStatisticError) as e:
        print(f"⛔ 자동 차단: {e}")
        return None, None, None

    issues = compliance_check(result.script)

    # 필수 고지 문구 누락은 "잘못된 정보"가 아니라 정형화된 법적 boilerplate가 빠진 것뿐이라,
    # 영상을 통째로 버리는 대신 자동으로 붙이고 재검사한다 (다른 위반은 그대로 차단).
    if issues == ["필수 고지 문구가 없음"]:
        result.script = result.script.rstrip() + " " + REQUIRED_DISCLAIMER
        issues = compliance_check(result.script)

    date_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    audio_path = os.path.join(OUTPUT_DIR, f"{date_tag}_narration.wav")
    video_path = os.path.join(OUTPUT_DIR, f"{date_tag}_short.mp4")
    photo_prefix = os.path.join(OUTPUT_DIR, f"{date_tag}_bg")
    metadata_path = os.path.join(OUTPUT_DIR, f"{date_tag}_metadata.json")
    _save_metadata(metadata_path, result, issues)

    print(f"제목: {result.title}")
    print(f"출처: {result.source or '(없음)'} / 검색 근거 {len(result.grounding_sources)}개")

    if issues:
        print("⛔ 자동 차단 (컴플라이언스 위반):")
        for issue in issues:
            print(f"  - {issue}")
        print(f"(대본 내용은 {metadata_path}에 남겨뒀습니다 — 나중에 확인 가능)")
        return None, None, None

    print("✅ 자동 점검 통과 — 음성/단어 타이밍 생성 중 (Typecast, 필재 보이스)...")
    narration_text = apply_pronunciation_fixes(result.script)
    audio_path, duration, words = generate_narration_with_words(narration_text, audio_path, voice_id=voice_id)
    # 발음용으로 바꿔치기했던 표기를 자막 텍스트에서는 원문 표기로 되돌린다(타이밍은 유지).
    for w in words:
        w.text = restore_original_spelling(w.text)

    print(f"배경 사진 검색 중... ({result.image_query})")
    photo_paths = search_photos(result.image_query, photo_prefix, count=3)
    if photo_paths:
        print(f"배경 사진 확보: {len(photo_paths)}장")
    else:
        print("배경 사진을 못 찾아서 그라데이션 배경으로 대체합니다.")

    print("영상 합성 중 (카라오케 자막)...")
    compose_short(result.title, words, audio_path, video_path, background_photo_paths=photo_paths or None)

    print(f"\n✅ 완료: {video_path}")
    print(f"메타데이터(스팟체크용): {metadata_path}")
    if upcoming_topic:
        remaining = len(topic_calendar.load_calendar())
        print(f"📅 다음 편 예고: {result.next_topic_hint} (캘린더 큐에 {remaining}개 남음)")
    else:
        print(f"📌 다음 편 예고(캘린더 미사용): {result.next_topic_hint}")
    return video_path, result, cluster


def run(topic: str | None = None, cluster: str | None = None, voice_id: str = VOICE_PILJAE) -> str | None:
    """영상만 만든다. 업로드는 하지 않는다 (수동으로 검토하고 싶을 때 사용)."""
    video_path, _, _ = _generate_and_compose(topic, cluster, voice_id)
    if video_path:
        print("업로드하려면 upload_and_comment()를 별도로 호출하세요 (자동 업로드하지 않습니다).")
    return video_path


def _publish_article(
    video_path: str, result: GeneratedScript, cluster: str, video_id: str, published_at: str
) -> None:
    """업로드된 영상의 대본을 그대로 웹사이트 아티클(web/content/articles/*.json)로도 발행한다.
    두 번 콘텐츠를 만들지 않고 "매거진 콘텐츠와 영상 소재 1:1 매칭"(실행 설계도 Phase 3)을
    달성하기 위함. 실패해도 영상 업로드 자체는 이미 끝난 상태라 예외를 삼키고 로그만 남긴다
    (사이트 반영이 하루 늦어지는 건 괜찮지만, 이미 끝난 업로드를 롤백할 이유는 없음)."""
    try:
        slug = slug_from_video_path(video_path)
        os.makedirs(ARTICLES_DIR, exist_ok=True)
        article_path = os.path.join(ARTICLES_DIR, f"{slug}.json")

        # 영상 만들 때 이미 받아둔 Pexels 배경사진(output/{date_tag}_bg_0.jpg)을 그대로 매거진
        # 썸네일로 재사용한다 — 새 이미지 API 호출도, 저작권 문제도 없음(같은 소스).
        date_tag = slug.replace("-", "_")
        source_photo = os.path.join(OUTPUT_DIR, f"{date_tag}_bg_0.jpg")
        thumbnail_rel_path = None
        if os.path.exists(source_photo):
            thumb_dir = os.path.join(REPO_ROOT, "web", "public", "magazine")
            os.makedirs(thumb_dir, exist_ok=True)
            thumb_path = os.path.join(thumb_dir, f"{slug}.jpg")
            shutil.copyfile(source_photo, thumb_path)
            thumbnail_rel_path = os.path.relpath(thumb_path, REPO_ROOT)

        with open(article_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "slug": slug,
                    "title": result.title,
                    "cluster": cluster,
                    "body": result.script,
                    "source": result.source,
                    "tags": result.tags,
                    "youtubeVideoId": video_id,
                    "publishedAt": published_at,
                    "thumbnailUrl": f"/magazine/{slug}.jpg" if thumbnail_rel_path else None,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # capture_output 텍스트에 한글 커밋 메시지가 섞여 있어서, Windows 기본 로케일(cp949)로
        # 디코딩하면 깨진다 — 인코딩을 명시해서 UnicodeDecodeError를 방지한다.
        rel_path = os.path.relpath(article_path, REPO_ROOT)
        add_paths = [rel_path] + ([thumbnail_rel_path] if thumbnail_rel_path else [])
        subprocess.run(["git", "add", *add_paths], cwd=REPO_ROOT, check=True)
        commit = subprocess.run(
            ["git", "commit", "-m", f"Publish article: {result.title}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
            print(f"⚠️ 아티클 git commit 실패: {commit.stdout}{commit.stderr}")
            return
        push = subprocess.run(
            ["git", "push"], cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8"
        )
        if push.returncode != 0:
            print(f"⚠️ 아티클 git push 실패: {push.stderr}")
        else:
            print(f"📰 웹사이트 아티클 발행됨: {rel_path}")
    except Exception as e:
        print(f"⚠️ 아티클 발행 중 오류(영상 업로드는 정상 완료됨): {e}")


def run_and_upload(
    topic: str | None = None,
    cluster: str | None = None,
    voice_id: str = VOICE_PILJAE,
    final_privacy: str = "public",
    scheduled_publish_at: str | None = "AUTO_7PM",
) -> dict | None:
    """영상 생성부터 업로드·댓글·공개 전환까지 사람 개입 없이 전부 끝낸다.
    WSL cron 등 무인 실행용 — daily_auto_run.py가 이 함수를 호출한다.

    scheduled_publish_at 기본값 "AUTO_7PM"은 실행 시점과 무관하게 항상 그날(KST) 오후 7시에
    유튜브가 자동으로 공개하도록 예약한다 (실행이 이미 오후 7시를 넘겼으면 다음날 오후 7시).
    cron이 새벽에 돌고 실제 시청자가 많은 저녁에 공개하고 싶어서 만든 옵션 — None을 넘기면
    즉시 공개(또는 final_privacy로 지정한 상태)로 바로 올라간다."""
    video_path, result, resolved_cluster = _generate_and_compose(topic, cluster, voice_id)
    if not video_path or not result:
        return None

    if scheduled_publish_at == "AUTO_7PM":
        scheduled_publish_at = next_publish_time_kst(19, 0)

    # _publish_article()이 같은 slug로 실제 파일을 커밋하는 건 업로드 성공 "이후"지만, slug
    # 자체는 video_path만으로 미리 결정되므로 설명란/댓글에 넣을 URL은 지금 만들어도 된다.
    article_url = f"{SITE_URL}/magazine/{slug_from_video_path(video_path)}"

    print("업로드 중...")
    upload_result = upload_and_comment(
        video_path=video_path,
        title=result.title,
        description=build_description(result, article_url),
        tags=result.tags,
        source=result.source,
        next_topic_hint=result.next_topic_hint,
        final_privacy=final_privacy,
        scheduled_publish_at=scheduled_publish_at,
        article_url=article_url,
    )
    print(f"업로드 결과: {upload_result}")

    if upload_result and upload_result.get("success"):
        published_at = scheduled_publish_at or datetime.now(KST).isoformat(timespec="seconds")
        _publish_article(video_path, result, resolved_cluster or "", upload_result["video_id"], published_at)

    return upload_result


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run()
    elif len(sys.argv) >= 3:
        run(sys.argv[1], sys.argv[2])
    else:
        print('사용법: python pipeline.py "주제" "클러스터"')
        print('예시:   python pipeline.py "물은 하루에 얼마나 마셔야 할까?" "영양 기초"')
        print('인자 없이 실행하면 topic_calendar.py로 미리 뽑아둔 큐에서 다음 주제를 자동으로 이어서 진행합니다.')
        sys.exit(1)
