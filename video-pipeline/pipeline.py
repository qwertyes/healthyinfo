"""
"오늘의 건강 상식" 숏폼 엔드투엔드 파이프라인.
대본 생성(Gemini) → 컴플라이언스 자동 점검 → 사람 검수(확인 프롬프트) → 음성/자막 생성 → 영상 합성.
업로드는 별도 확인을 거쳐야 해서 이 스크립트에서 자동으로 하지 않는다 — 마지막에 안내만 출력한다.

실행: python pipeline.py "단백질은 하루에 얼마나 먹어야 할까?" "영양 기초"
"""

import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

from compose_video import compose_short
from script_prompt import ScriptRequest, generate_script
from tts import VOICE_FEMALE, generate_narration_with_captions_sync

# COMPLIANCE_COPY_GUIDE.md의 금지 표현 목록 — 자동 1차 점검용 (사람 검수를 대체하지 않음)
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


def human_review(result: dict) -> bool:
    """생성된 대본을 화면에 보여주고 사람이 진행 여부를 결정한다."""
    print("\n" + "=" * 60)
    print(f"제목: {result['title']}")
    print("-" * 60)
    print(result["script"])
    print("-" * 60)
    print(f"출처: {result['source'] or '(없음)'}")
    print(f"태그: {', '.join(result['tags'])}")
    print("=" * 60)

    issues = compliance_check(result["script"])
    if issues:
        print("\n⚠️ 자동 점검 경고:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 자동 점검 통과 (금지 표현 없음, 고지 문구 있음)")

    answer = input("\n이 대본으로 영상을 만들까요? [y/N]: ").strip().lower()
    return answer == "y"


def run(topic: str, cluster: str, voice: str = VOICE_FEMALE) -> str | None:
    print(f"대본 생성 중... (주제: {topic})")
    result = generate_script(ScriptRequest(topic=topic, cluster=cluster))

    if not human_review(result):
        print("취소되었습니다.")
        return None

    date_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    audio_path = os.path.join(OUTPUT_DIR, f"{date_tag}_narration.mp3")
    video_path = os.path.join(OUTPUT_DIR, f"{date_tag}_short.mp4")

    print("음성/자막 생성 중...")
    audio_path, captions = generate_narration_with_captions_sync(result["script"], audio_path, voice=voice)

    print("영상 합성 중...")
    compose_short(result["title"], captions, audio_path, video_path)

    print(f"\n✅ 완료: {video_path}")
    print("업로드하려면 youtube_upload.upload_video()를 별도로 호출하세요 (자동 업로드하지 않습니다).")
    return video_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('사용법: python pipeline.py "주제" "클러스터"')
        print('예시:   python pipeline.py "물은 하루에 얼마나 마셔야 할까?" "영양 기초"')
        sys.exit(1)

    run(sys.argv[1], sys.argv[2])
