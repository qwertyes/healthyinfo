"""
건강정보 숏폼 내레이션용 TTS 생성 모듈.
Microsoft Edge TTS(edge-tts) 사용 — API 키/계정 없이 바로 동작.
my-video-creator의 make_tts.py와 달리 특정 원고에 하드코딩되지 않은 재사용 가능한 함수로 작성.
"""

import asyncio
import os
import edge_tts

VOICE_FEMALE = "ko-KR-SunHiNeural"
VOICE_MALE = "ko-KR-InJoonNeural"


async def generate_narration(text: str, out_path: str, voice: str = VOICE_FEMALE, rate: str = "+0%") -> str:
    """text를 voice로 내레이션 음성 파일(out_path, mp3)로 생성한다."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(out_path)
    return out_path


def generate_narration_sync(text: str, out_path: str, voice: str = VOICE_FEMALE, rate: str = "+0%") -> str:
    return asyncio.run(generate_narration(text, out_path, voice=voice, rate=rate))


if __name__ == "__main__":
    # 동작 확인용 샘플 — 실제 대본 생성 파이프라인(script_prompt.py) 연결 전 TTS 모듈만 단독 검증
    sample_text = (
        "오늘의 건강 상식입니다. 단백질은 근육뿐 아니라 면역력 유지에도 중요한 역할을 합니다. "
        "일반적으로 체중 1킬로그램당 하루 1점 2그램에서 1점 6그램 정도가 권장된다고 알려져 있습니다. "
        "이 정보는 일반적인 영양 정보이며, 의학적 진단이나 치료를 대체하지 않습니다."
    )
    out = generate_narration_sync(sample_text, "video-pipeline/samples/sample_female.mp3", voice=VOICE_FEMALE)
    print(f"생성 완료: {out}")
