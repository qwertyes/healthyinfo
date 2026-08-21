"""
Typecast API 기반 내레이션 TTS — 단어 단위 타임스탬프 포함.
edge-tts(tts.py)는 한국어 문장 단위 타이밍만 지원했지만, Typecast는 단어 단위 타이밍을
줘서 카라오케 스타일(말하는 단어 하이라이트) 자막을 만들 수 있다.

목소리: "필재"(Piljae) — 지식/정보성 콘텐츠(역사, 사건사고 등)에 인기 있는 목소리로 확인됨
(https://typecast.ai/kr/learn/typecast-piljae-ai-voice-youtube-shorts/), 우리 콘텐츠(건강 상식)와
같은 장르라 선택했다.
"""

import base64
import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.typecast.ai/v1/text-to-speech/with-timestamps"
VOICE_PILJAE = "tc_68257f68bc6e3c161ab5078d"
MODEL = "ssfm-v30"


@dataclass
class WordTiming:
    text: str
    start: float
    end: float


def generate_narration_with_words(
    text: str, out_path: str, voice_id: str = VOICE_PILJAE
) -> tuple[str, float, list[WordTiming]]:
    """
    내레이션 오디오(wav)를 생성하고, 단어 단위 타이밍을 함께 반환한다.
    반환: (오디오 파일 경로, 전체 길이(초), 단어 타이밍 목록)
    """
    api_key = os.environ.get("TYPECAST_API_KEY")
    if not api_key:
        raise RuntimeError("환경변수 TYPECAST_API_KEY가 설정되어 있지 않습니다.")

    response = requests.post(
        API_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        params={"granularity": "word"},
        json={
            "voice_id": voice_id,
            "text": text,
            "model": MODEL,
            "output": {"audio_format": "wav"},
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    audio_bytes = base64.b64decode(data["audio"])
    with open(out_path, "wb") as f:
        f.write(audio_bytes)

    words = [WordTiming(text=w["text"], start=w["start"], end=w["end"]) for w in data.get("words", [])]
    return out_path, data["audio_duration"], words


if __name__ == "__main__":
    sample_text = (
        "오늘의 건강 상식입니다. 단백질은 근육뿐 아니라 면역력 유지에도 중요한 역할을 합니다. "
        "이 정보는 일반적인 영양 정보이며, 의학적 진단이나 치료를 대체하지 않습니다."
    )
    path, duration, words = generate_narration_with_words(sample_text, "video-pipeline/samples/typecast_sample.wav")
    print(f"생성 완료: {path} ({duration:.2f}초)")
    for w in words:
        print(f"  [{w.start:.2f}-{w.end:.2f}] {w.text}")
