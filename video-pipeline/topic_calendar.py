"""
클러스터별로 영상 주제를 여러 개 미리 브레인스토밍해서 큐로 쌓아두는 모듈.

기존 방식(영상 하나 만들 때마다 그 대본이 예고한 주제 하나만 다음 실행에 이어받는 체인,
pipeline.py의 옛 content_queue.json)은 "영상을 만들면서 그때그때 다음 제목이 정해지는" 구조라
진짜 사전 기획이 아니라는 피드백을 받았다. 이 모듈은 PLAN.md의 5개 콘텐츠 클러스터
(영양 기초 / 증상별 가이드 / 식단 비교 / 제품 큐레이션 / 루틴·기록) 각각에서 주제를 여러 개
한 번에 뽑아 라운드로빈으로 섞은 큐를 content_calendar.json에 저장해둔다.
pipeline.py는 인자 없이 실행되면 이 큐에서 하나씩 꺼내 쓴다.

주제 브레인스토밍은 사실 검증이 필요 없는 단계라 검색 그라운딩 없이 순수 생성만 한다.
실제 대본 작성(script_prompt.generate_script)은 여전히 검색 그라운딩 + 컴플라이언스 검증을
거친다 — 이 모듈은 "무엇을 다룰지"만 미리 정할 뿐, "어떻게 쓸지"는 매번 새로 검증한다.

실행: python topic_calendar.py [클러스터당_주제_개수(기본 5)]
"""

import json
import os
import sys

import google.genai as genai
from dotenv import load_dotenv
from google.genai import types as genai_types

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CALENDAR_PATH = os.path.join(BASE_DIR, "content_calendar.json")
MODEL_NAME = "gemini-3.1-flash-lite"

CLUSTERS = ["영양 기초", "증상별 가이드", "식단 비교", "제품 큐레이션", "루틴·기록"]

_CLUSTER_HINTS = {
    "영양 기초": "영양소, 하루 권장량, 특정 성분의 역할처럼 기초적인 영양 상식",
    "증상별 가이드": "피로, 부종, 소화불량처럼 흔한 증상과 식습관의 관계",
    "식단 비교": "간헐적 단식 vs 규칙적 식사, 저탄고지 vs 균형식처럼 서로 다른 식단 방식의 비교",
    "제품 큐레이션": "유산균, 오메가3 같은 특정 식품군을 고를 때 확인할 기준 (특정 브랜드·제품명은 금지)",
    "루틴·기록": "식사 시간, 물 섭취량, 식사 순서 같은 일상 습관과 건강의 관계",
}

TOPIC_SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["topics"],
}

SYSTEM_PROMPT = """당신은 한끼정답 유튜브 채널의 콘텐츠 기획자입니다. 실제 대본은 나중에
별도로 검색 검증을 거쳐 작성되므로, 지금은 "검증 가능할 법한, 시청자가 궁금해할 구체적인
질문형 주제"만 뽑으면 됩니다.

- 질병의 치료·완치를 단정하는 주제, 특정 브랜드·제품명을 다루는 주제는 제안하지 마세요.
- "건강한 식습관이란?"처럼 뻔하고 추상적인 주제 대신, 구체적이고 궁금증을 유발하는 질문형
  주제를 쓰세요. 예: "저녁 늦게 먹으면 정말 살이 더 찔까?"
- 제안하는 주제끼리도, 그리고 이미 다룬 주제와도 겹치지 않게 하세요."""


def _existing_topics() -> list[str]:
    """중복 방지용으로 이미 만든 영상 제목들을 모은다."""
    titles = []
    if not os.path.isdir(OUTPUT_DIR):
        return titles
    for name in os.listdir(OUTPUT_DIR):
        if not name.endswith("_metadata.json"):
            continue
        try:
            with open(os.path.join(OUTPUT_DIR, name), encoding="utf-8") as f:
                title = json.load(f).get("title", "")
        except (json.JSONDecodeError, OSError):
            continue
        if title:
            titles.append(title)
    return titles


def generate_topics_for_cluster(client: genai.Client, cluster: str, count: int, avoid: list[str]) -> list[str]:
    avoid_text = "\n".join(f"- {t}" for t in avoid) if avoid else "(없음)"
    prompt = (
        f"클러스터: {cluster}\n"
        f"이 클러스터의 성격: {_CLUSTER_HINTS.get(cluster, '')}\n\n"
        f"이미 다룬 주제(겹치지 않게 하세요):\n{avoid_text}\n\n"
        f"이 클러스터에 맞는 새로운 영상 주제를 {count}개 제안하세요."
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_json_schema=TOPIC_SCHEMA,
            temperature=1.0,
        ),
    )
    data = json.loads(response.text)
    return data["topics"][:count]


def build_calendar(topics_per_cluster: int = 5) -> list[dict]:
    """5개 클러스터 각각에서 topics_per_cluster개씩 뽑아, 라운드로빈으로 섞은 큐를 만든다
    (한 클러스터 주제로 몰리지 않고 골고루 섞여서 나오게)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("환경변수 GEMINI_API_KEY가 설정되어 있지 않습니다.")
    client = genai.Client(api_key=api_key)

    avoid = _existing_topics()
    per_cluster: dict[str, list[str]] = {}
    for cluster in CLUSTERS:
        topics = generate_topics_for_cluster(client, cluster, topics_per_cluster, avoid)
        per_cluster[cluster] = topics
        avoid = avoid + topics  # 다른 클러스터끼리도 겹치지 않게 계속 누적해서 피한다

    queue = []
    for i in range(topics_per_cluster):
        for cluster in CLUSTERS:
            topics = per_cluster[cluster]
            if i < len(topics):
                queue.append({"topic": topics[i], "cluster": cluster})
    return queue


def load_calendar() -> list[dict]:
    if not os.path.exists(CALENDAR_PATH):
        return []
    with open(CALENDAR_PATH, encoding="utf-8") as f:
        return json.load(f).get("queue", [])


def save_calendar(queue: list[dict]) -> None:
    with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump({"queue": queue}, f, ensure_ascii=False, indent=2)


def pop_next() -> tuple[dict | None, dict | None]:
    """큐에서 오늘 만들 항목을 꺼내고, 그 다음 항목(대본 마지막 예고용)도 미리 알려준다.
    반환: (오늘 항목, 다음 항목). 큐가 비어있으면 (None, None)."""
    queue = load_calendar()
    if not queue:
        return None, None
    today = queue.pop(0)
    save_calendar(queue)
    upcoming = queue[0] if queue else None
    return today, upcoming


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"클러스터 5개 x {count}개씩 주제 브레인스토밍 중...")
    new_queue = build_calendar(topics_per_cluster=count)
    save_calendar(new_queue)
    print(f"완료: {len(new_queue)}개 주제를 {CALENDAR_PATH}에 저장했습니다.\n")
    for i, item in enumerate(new_queue, 1):
        print(f"{i}. [{item['cluster']}] {item['topic']}")
