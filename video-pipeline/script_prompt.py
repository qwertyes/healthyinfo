"""
건강정보 숏폼 대본 생성 프롬프트.
COMPLIANCE_COPY_GUIDE.md의 가드레일을 시스템 프롬프트에 고정 삽입한다.

실제 LLM 호출(Gemini 등)은 Vercel/Supabase 계정 및 API 키가 준비된 뒤 연결한다.
지금은 프롬프트 템플릿과 출력 스키마만 정의해 둔다 — Phase 2의 "사람 검수" 단계에서
이 스키마의 script/source/disclaimer 필드를 검수자가 그대로 확인할 수 있게 설계했다.
"""

from dataclasses import dataclass

SYSTEM_PROMPT = """당신은 한끼정답 유튜브 채널의 건강정보 숏폼 대본 작가입니다.
아래 규칙을 반드시 지키세요 (위반 시 콘텐츠가 발행되지 않습니다):

1. 특정 질병의 예방, 치료, 완치를 단정하지 마세요.
2. "치료", "처방", "주치의" 등 의료 행위를 암시하는 단어를 쓰지 마세요.
3. 특정 식품·영양제와 질병 효능을 직접 연결하지 마세요.
4. 불확실한 내용은 "~로 알려져 있다", "~라는 연구 결과가 있다"처럼 단정하지 않는 어투로 쓰세요.
5. 의학적 주장에는 반드시 출처(연구명, 공공기관명 등)를 함께 제시하세요. 출처를 특정할 수 없으면
   그 문장 자체를 넣지 마세요.
6. 60초 낭독 기준(약 350~420자)의 한국어 대본을 작성하세요. 첫 문장은 시청자의 호기심을
   끄는 후킹 문장이어야 합니다.
7. 마지막 문장은 항상 다음 고지 문구로 마무리하세요:
   "이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다."

출력은 반드시 아래 JSON 스키마를 따르세요:
{
  "title": "영상 제목 (후킹 문구 포함, 40자 이내)",
  "script": "실제 낭독할 전체 대본 (고지 문구 포함)",
  "source": "인용한 출처 (연구/공공기관명). 없으면 빈 문자열",
  "tags": ["영상 태그", "..."]
}"""


@dataclass
class ScriptRequest:
    topic: str
    cluster: str  # PLAN.md의 콘텐츠 클러스터: 영양 기초 / 증상별 가이드 / 식단 비교 / 제품 큐레이션 / 루틴·기록


def build_user_prompt(request: ScriptRequest) -> str:
    return (
        f"콘텐츠 클러스터: {request.cluster}\n"
        f"오늘의 주제: {request.topic}\n\n"
        "위 주제로 '오늘의 건강 상식' 시리즈용 60초 숏폼 대본을 시스템 프롬프트 규칙에 맞춰 작성해줘."
    )


def generate_script(request: ScriptRequest) -> dict:
    """
    실제 LLM 호출부. Vercel AI Gateway API 키가 설정되면 여기서 모델을 호출하도록 구현한다.
    지금은 계정/키가 없어 연결하지 않은 상태 — 호출 시 명시적으로 실패한다.
    """
    raise NotImplementedError(
        "LLM API가 아직 연결되지 않았습니다. Vercel AI Gateway API 키 설정 후 "
        "이 함수 안에서 SYSTEM_PROMPT + build_user_prompt(request)로 모델을 호출하도록 구현하세요."
    )


if __name__ == "__main__":
    sample = ScriptRequest(topic="단백질은 하루에 얼마나 먹어야 할까?", cluster="영양 기초")
    print(SYSTEM_PROMPT)
    print("\n---\n")
    print(build_user_prompt(sample))
