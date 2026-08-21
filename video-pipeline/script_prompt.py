"""
건강정보 숏폼 대본 생성 프롬프트.
COMPLIANCE_COPY_GUIDE.md의 가드레일을 시스템 프롬프트에 고정 삽입한다.

완전 자동화(사람 검수 없음) 운영을 위해 Google 검색 그라운딩을 사용한다 — 모델이 실제로
검색한 근거 없이 만든 대본은 UnverifiedContentError로 자동 차단된다. 검수 시간이 없는 대신,
"검증 안 된 통계는 아예 발행하지 않는다"를 기계적으로 강제하는 것으로 대체했다.

LLM 호출은 Gemini를 직접 사용한다 (web/src/app/api/meal-plan/route.ts와 동일한 GEMINI_API_KEY,
my-video-creator/test_gemini_api.py와 동일한 google-genai 클라이언트 패턴).
"""

import json
import os
from dataclasses import dataclass, field

import google.genai as genai
from dotenv import load_dotenv
from google.genai import types as genai_types

load_dotenv()

MODEL_NAME = "gemini-3.1-flash-lite"  # my-video-creator와 동일한 저비용 티어

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "script": {"type": "string"},
        "source": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "image_query": {"type": "string"},
    },
    "required": ["title", "script", "source", "tags", "image_query"],
}

SYSTEM_PROMPT = """당신은 한끼정답 유튜브 채널의 건강정보 숏폼 대본 작가입니다.
이 채널의 존재 이유는 "듣고 나면 실제로 도움이 되고, 다음 편도 궁금해지는" 정보를 주는 것입니다.
알맹이 없이 안전하기만 한 대본은 컴플라이언스를 지켰어도 실패작입니다.

이 작업에는 사람 검수가 없습니다 — 당신이 사실 확인의 마지막 단계입니다. 아래 규칙을 반드시
지키세요 (위반 시 콘텐츠가 발행되지 않습니다):

[사실 확인 — 가장 중요]
1. 아래 "검색으로 확인된 사실" 섹션에 제공된 내용만 근거로 사용하세요. 거기 없는 통계·연구명·
   기관명을 새로 지어내면 절대 안 됩니다.
2. 제공된 사실 중에서도 신뢰도 우선순위를 지키세요: ① 정부·공공기관(예: 식품의약품안전처,
   보건복지부, 질병관리청, WHO) ② 학회·대학·의료기관 ③ 학술지에 게재된 연구. 쇼핑몰, 특정
   제품 판매 사이트, 개인 블로그, 출처 불명 커뮤니티 글은 근거로 삼지 마세요 — 그런 출처밖에
   없다면 그 수치는 대본에서 빼세요.
3. 제공된 사실 중 신뢰할 만한 게 없다면, 자극적인 수치를 억지로 만들어내지 말고 일반적으로
   잘 알려진 상식 수준의 정보로 대본을 구성하세요 — 이런 공개된 일반 정보도 시청자에게는
   충분히 의미 있는 정보입니다.

[정보 밀도]
4. 반드시 구체적인 사실을 1~2개 이상 포함하세요 (숫자, 비교, 방법 이름, 조건 등 — 단, 위 사실
   확인 규칙을 지킨 것만). "사람마다 다릅니다", "전문가와 상담하세요", "균형이 중요합니다" 같은
   알맹이 없는 문장으로 본문을 채우거나 결론을 내리지 마세요.
5. "OO이 나에게 맞을까?"처럼 개인차가 있는 주제라도, 판단 기준이 되는 구체적 조건을
   제시하세요. 예: "이런 특징이 있다면 적합하고, 이런 경우엔 맞지 않을 수 있다."
6. 대본의 마지막 문장(필수 고지 문구 바로 앞)에는, 시청자가 다음 영상도 보고 싶어지도록
   관련된 흥미로운 질문이나 다음에 다룰 만한 소재를 자연스럽게 한 줄 남기세요.

[컴플라이언스]
7. 특정 질병의 예방, 치료, 완치를 단정하지 마세요.
8. "치료", "처방", "주치의" 등 의료 행위를 암시하는 단어를 쓰지 마세요.
9. 특정 식품·영양제와 질병 효능을 직접 연결하지 마세요.
10. 불확실한 내용은 "~로 알려져 있다"처럼 단정하지 않는 어투로 쓰되, 정보 자체는 구체적으로.
11. 실제로 검색해서 확인한 출처(기관명 등)를 "source" 필드에 명시하세요.

[형식]
12. 60초 낭독 기준(약 350~420자)의 한국어 대본. 첫 문장은 후킹 문장이어야 합니다.
13. 마지막 문장은 항상 다음 고지 문구로 마무리하세요:
   "이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다."
14. "image_query"에는 영상 배경으로 쓸 스톡 사진을 검색할 **영어** 키워드를 2~4단어로 쓰세요.
   구체적이고 눈에 보이는 대상을 묘사하세요 (예: "grilled chicken breast", "person drinking water",
   "fresh vegetables market"). 추상적인 개념어(예: "health", "nutrition")만 쓰지 마세요.

출력은 반드시 아래 JSON 스키마를 따르세요:
{
  "title": "영상 제목 (후킹 문구 포함, 40자 이내)",
  "script": "실제 낭독할 전체 대본 (고지 문구 포함)",
  "source": "실제 검색으로 확인한 출처 (기관/연구명). 일반 상식 수준이라 특정 출처가 없으면 빈 문자열",
  "tags": ["영상 태그", "..."],
  "image_query": "배경 사진 검색용 영어 키워드"
}"""


class UnverifiedContentError(Exception):
    """모델이 검색 그라운딩 없이(=사실 확인 없이) 답변한 경우 발생 — 사람 검수가 없으므로 자동 차단한다."""


@dataclass
class ScriptRequest:
    topic: str
    cluster: str  # PLAN.md의 콘텐츠 클러스터: 영양 기초 / 증상별 가이드 / 식단 비교 / 제품 큐레이션 / 루틴·기록


@dataclass
class GeneratedScript:
    title: str
    script: str
    source: str
    tags: list[str]
    image_query: str
    grounding_sources: list[dict] = field(default_factory=list)  # [{"title":.., "uri":..}, ...] 실제 검색 근거


def build_user_prompt(request: ScriptRequest) -> str:
    return (
        f"콘텐츠 클러스터: {request.cluster}\n"
        f"오늘의 주제: {request.topic}\n\n"
        "아래에 제공되는 '검색으로 확인된 사실'만 근거로 삼아서, '오늘의 건강 상식' 시리즈용 "
        "60초 숏폼 대본을 시스템 프롬프트 규칙에 맞춰 작성해줘."
    )


def _research_facts(client: genai.Client, request: ScriptRequest, max_attempts: int = 3):
    """
    1단계(리서치 전용 호출): 순수하게 검색만 시킨다. 시스템 프롬프트도, 스키마도 없이 검색
    지시 하나만 주는 게 훨씬 안정적으로 검색을 트리거한다 — 복잡한 규칙과 함께 주면(2단계처럼)
    모델이 검색 도구 호출을 건너뛰는 경우가 많다는 걸 테스트로 확인했다.
    반환: (검색으로 정리된 텍스트, [{"title":.., "uri":..}, ...])
    """
    prompt = (
        f"'{request.topic}'에 대해 Google 검색으로 신뢰할 수 있는 최신 정보를 찾아줘. "
        "구체적인 수치와 출처를 포함해서 정리해줘. 정부기관·학회·학술지 등 공신력 있는 출처를 "
        "우선하고, 쇼핑몰이나 개인 블로그는 근거로 쓰지 마."
    )
    config = genai_types.GenerateContentConfig(
        tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
    )

    for attempt in range(1, max_attempts + 1):
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt, config=config)
        grounding_metadata = response.candidates[0].grounding_metadata
        grounding_chunks = grounding_metadata.grounding_chunks if grounding_metadata else None
        if grounding_chunks:
            sources = [
                {"title": c.web.title, "uri": c.web.uri} for c in grounding_chunks if getattr(c, "web", None)
            ]
            return response.text, sources

    return None, []


def generate_script(request: ScriptRequest) -> GeneratedScript:
    """
    2단계로 나눠서 생성한다: ① 검색 전용 호출로 사실을 모으고 ② 그 사실만 근거로 삼아
    컴플라이언스 규칙에 맞춰 대본을 작성한다. ①에서 검색 근거를 하나도 못 찾으면
    UnverifiedContentError — 사람 검수가 없는 자동화 파이프라인의 최소 안전장치다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("환경변수 GEMINI_API_KEY가 설정되어 있지 않습니다.")

    client = genai.Client(api_key=api_key)

    facts_text, sources = _research_facts(client, request)
    if not sources:
        raise UnverifiedContentError(
            f"'{request.topic}' 주제에 대해 검색 근거를 찾지 못했습니다 — 사실 확인이 안 된 "
            "내용일 수 있어 자동으로 차단합니다. 주제를 바꿔서 다시 시도하세요."
        )

    writing_prompt = (
        f"{build_user_prompt(request)}\n\n"
        f"검색으로 확인된 사실:\n{facts_text}"
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=writing_prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_json_schema=RESPONSE_SCHEMA,
            temperature=0.8,
        ),
    )

    data = json.loads(response.text)
    return GeneratedScript(
        title=data["title"],
        script=data["script"],
        source=data["source"],
        tags=data["tags"],
        image_query=data["image_query"],
        grounding_sources=sources,
    )


if __name__ == "__main__":
    sample = ScriptRequest(topic="단백질은 하루에 얼마나 먹어야 할까?", cluster="영양 기초")
    result = generate_script(sample)
    print(f"제목: {result.title}")
    print(f"대본: {result.script}")
    print(f"출처(자체 기재): {result.source}")
    print(f"태그: {result.tags}")
    print(f"이미지 검색어: {result.image_query}")
    print("검색 그라운딩 근거:")
    for s in result.grounding_sources:
        print(f"  - {s['title']}: {s['uri']}")
