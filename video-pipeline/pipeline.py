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
                "grounding_sources": result.grounding_sources,
                "compliance_issues": issues,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def run(topic: str, cluster: str, voice_id: str = VOICE_PILJAE) -> str | None:
    print(f"대본 생성 중... (주제: {topic})")
    try:
        result = generate_script(ScriptRequest(topic=topic, cluster=cluster))
    except UnverifiedContentError as e:
        print(f"⛔ 자동 차단: {e}")
        return None

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

    print(f"\n✅ 완료: {video_path}")
    print(f"메타데이터(스팟체크용): {metadata_path}")
    print("업로드하려면 youtube_upload.upload_video()를 별도로 호출하세요 (자동 업로드하지 않습니다).")
    return video_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('사용법: python pipeline.py "주제" "클러스터"')
        print('예시:   python pipeline.py "물은 하루에 얼마나 마셔야 할까?" "영양 기초"')
        sys.exit(1)

    run(sys.argv[1], sys.argv[2])
