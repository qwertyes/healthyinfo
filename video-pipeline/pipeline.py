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
import sys
from datetime import datetime

# Windows 콘솔 기본 코드페이지(cp949)가 이모지(⛔✅)를 못 그려서 print()가 죽는 문제 방지.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

from compose_video import compose_short
from script_prompt import GeneratedScript, ScriptRequest, UnverifiedContentError, generate_script
from stock_photo import search_photos
from typecast_tts import VOICE_PILJAE, generate_narration_with_words

# COMPLIANCE_COPY_GUIDE.md의 금지 표현 목록 — 자동 점검용 (사람 검수 없이 이게 최종 게이트)
BANNED_PATTERNS = [
    "치료합니다", "치료됩니다", "완치", "처방", "주치의", "AI 의사", "AI 주치의",
    "낫습니다", "낫는다", "질병을 예방합니다",
]

REQUIRED_DISCLAIMER = "이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다."

# 대본이 "다음 영상 예고"로 남긴 주제를 실제로 이어가기 위한 큐. 영상이 하나 완성될 때마다
# 그 대본의 next_topic_hint로 덮어써서, 다음 실행이 인자 없이도 그 주제를 이어받게 한다.
QUEUE_PATH = os.path.join(BASE_DIR, "content_queue.json")


def _load_queue() -> dict | None:
    if not os.path.exists(QUEUE_PATH):
        return None
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_queue(next_topic: str, cluster: str, promised_by_title: str, promised_by_video: str) -> None:
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "next_topic": next_topic,
                "cluster": cluster,
                "promised_by_title": promised_by_title,
                "promised_by_video": promised_by_video,
                "queued_at": datetime.now().isoformat(),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


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


def run(topic: str | None = None, cluster: str | None = None, voice_id: str = VOICE_PILJAE) -> str | None:
    if topic is None:
        queue_entry = _load_queue()
        if not queue_entry:
            print("⛔ 대기 중인 예고 주제가 없습니다. 주제를 직접 지정해서 실행하세요:")
            print('   python pipeline.py "주제" "클러스터"')
            return None
        topic = queue_entry["next_topic"]
        cluster = cluster or queue_entry["cluster"]
        print(f"📌 이전 영상('{queue_entry['promised_by_title']}')이 예고한 주제를 이어서 진행합니다.")
    elif cluster is None:
        raise ValueError("topic을 직접 지정할 때는 cluster도 함께 지정해야 합니다.")

    print(f"대본 생성 중... (주제: {topic})")
    try:
        result = generate_script(ScriptRequest(topic=topic, cluster=cluster))
    except UnverifiedContentError as e:
        print(f"⛔ 자동 차단: {e}")
        return None

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
        return None

    print("✅ 자동 점검 통과 — 음성/단어 타이밍 생성 중 (Typecast, 필재 보이스)...")
    audio_path, duration, words = generate_narration_with_words(result.script, audio_path, voice_id=voice_id)

    print(f"배경 사진 검색 중... ({result.image_query})")
    photo_paths = search_photos(result.image_query, photo_prefix, count=3)
    if photo_paths:
        print(f"배경 사진 확보: {len(photo_paths)}장")
    else:
        print("배경 사진을 못 찾아서 그라데이션 배경으로 대체합니다.")

    print("영상 합성 중 (카라오케 자막)...")
    compose_short(result.title, words, audio_path, video_path, background_photo_paths=photo_paths or None)

    _save_queue(result.next_topic_hint, cluster, result.title, video_path)

    print(f"\n✅ 완료: {video_path}")
    print(f"메타데이터(스팟체크용): {metadata_path}")
    print(f"📌 다음 예고 주제 저장됨: {result.next_topic_hint} (다음엔 인자 없이 실행하면 이어받습니다)")
    print("업로드하려면 youtube_upload.upload_video()를 별도로 호출하세요 (자동 업로드하지 않습니다).")
    return video_path


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run()
    elif len(sys.argv) >= 3:
        run(sys.argv[1], sys.argv[2])
    else:
        print('사용법: python pipeline.py "주제" "클러스터"')
        print('예시:   python pipeline.py "물은 하루에 얼마나 마셔야 할까?" "영양 기초"')
        print('인자 없이 실행하면 이전 영상이 예고한 다음 주제를 자동으로 이어서 진행합니다.')
        sys.exit(1)
