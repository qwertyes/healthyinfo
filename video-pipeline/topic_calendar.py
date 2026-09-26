"""
클러스터별로 영상 주제를 여러 개 미리 브레인스토밍해서 큐로 쌓아두는 모듈.

기존 방식(영상 하나 만들 때마다 그 대본이 예고한 주제 하나만 다음 실행에 이어받는 체인,
pipeline.py의 옛 content_queue.json)은 "영상을 만들면서 그때그때 다음 제목이 정해지는" 구조라
진짜 사전 기획이 아니라는 피드백을 받았다. 이 모듈은 CLUSTERS(한식 밥상 해부 / 편의점·배달 한끼 / 조리·보관의 과학 / 성분표 읽기 /
시즌·상황별 한끼 / 음료·간식) 각각에서 주제를 여러 개 한 번에 뽑아 비중에 맞게 섞은 큐를
content_calendar.json에 저장해둔다.
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

WEB_ARTICLES_DIR = os.path.join(BASE_DIR, "..", "web", "content", "articles")

# 기존 5개 클러스터(영양 기초/증상별 가이드/식단 비교/제품 큐레이션/루틴·기록)는 혈당 스파이크·
# 식사 시간·영양제 고르기 쪽으로 주제가 계속 겹쳐서, 한끼정답 채널 성격에 맞는 새 방향으로 교체했다.
CLUSTERS = ["한식 밥상 해부", "편의점·배달 한끼", "조리·보관의 과학", "성분표 읽기", "시즌·상황별 한끼", "음료·간식"]

# 큐에서 차지하는 비중 — 채널에 가장 잘 맞는 "한식 밥상 해부"를 다른 클러스터의 2배로 뽑는다.
CLUSTER_WEIGHTS = {"한식 밥상 해부": 2}

_CLUSTER_HINTS = {
    "한식 밥상 해부": "김치·된장·국물·나물·밥·반찬처럼 매일 먹는 한식 한 가지를 골라 영양·나트륨·먹는 방법을 해부하는 주제 (예: 김치찌개 국물, 된장국 건더기, 라면 국물 vs 곰탕 국물)",
    "편의점·배달 한끼": "삼각김밥·김밥·샌드위치·국밥·치킨처럼 편의점·배달 한 끼를 종류별로 비교하고 고르는 법 (특정 브랜드·제품명은 금지)",
    "조리·보관의 과학": "삶기·찌기·굽기·튀기기, 에어프라이어, 튀김 기름 재사용, 냉동 vs 신선, 통조림처럼 같은 재료를 어떻게 다루느냐에 따른 차이",
    "성분표 읽기": "영양성분표·식품표시의 특정 항목 하나(제로 표기, 1회 제공량, 당류 vs 첨가당, 나트륨 표시 등)를 읽는 법 — '뒷면 확인하세요' 같은 뻔한 주제는 금지",
    "시즌·상황별 한끼": "가을 제철 식재료, 명절 음식 후 속, 야근 후 야식, 해장국처럼 시기·상황에 맞는 한 끼 이야기",
    "음료·간식": "제로 음료·감미료, 에너지드링크 카페인, 커피, 소금 종류, 과자·견과·프로틴바처럼 매일 사 먹는 음료와 간식",
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
  주제를 쓰세요. 예: "김치찌개 국물까지 다 먹으면 나트륨은 얼마나 될까?"
- 제안하는 주제끼리도, 그리고 이미 다룬 주제와도 겹치지 않게 하세요. 제목 표현만 바꾼
  같은 내용(예: 이미 다룬 '식후 30분 산책'을 '식후 걷기'로 바꾼 것)도 겹친 것으로 봅니다.
- 혈당 스파이크, 식사 시간, 영양제·유산균·오메가3 고르기는 이미 충분히 다뤘으니 피하세요.
- "몇 퍼센트 더 좋다"처럼 구체적인 수치가 있어야 성립하는 주제는 피하고, 식약처·보건복지부
  등 공공기관 자료로 확인할 수 있는 주제를 우선하세요."""


def _titles_in_dir(directory: str, suffix: str) -> list[str]:
    titles = []
    if not os.path.isdir(directory):
        return titles
    for name in os.listdir(directory):
        if not name.endswith(suffix):
            continue
        try:
            with open(os.path.join(directory, name), encoding="utf-8") as f:
                title = json.load(f).get("title", "")
        except (json.JSONDecodeError, OSError):
            continue
        if title:
            titles.append(title)
    return titles


def _existing_topics() -> list[str]:
    """중복 방지용으로 이미 만든 영상 제목들을 모은다. output/에는 최근 파일만 남아 있어서,
    영상마다 1:1로 쌓이는 웹 아티클(web/content/articles)까지 함께 본다."""
    titles = _titles_in_dir(OUTPUT_DIR, "_metadata.json") + _titles_in_dir(WEB_ARTICLES_DIR, ".json")
    return list(dict.fromkeys(titles))  # 순서를 유지하면서 중복 제거


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


def _round_robin_queue(client: genai.Client, topics_per_cluster: int, avoid: list[str]) -> list[dict]:
    """클러스터마다 topics_per_cluster개(CLUSTER_WEIGHTS가 있으면 그 배수)씩 뽑아, 한 클러스터
    주제로 몰리지 않게 비중에 비례해서 고르게 섞은 큐를 만든다."""
    ordered = []  # (큐 안에서의 상대 위치, 클러스터, 주제)
    for cluster in CLUSTERS:
        count = topics_per_cluster * CLUSTER_WEIGHTS.get(cluster, 1)
        topics = generate_topics_for_cluster(client, cluster, count, avoid)
        avoid = avoid + topics  # 다른 클러스터끼리도 겹치지 않게 계속 누적해서 피한다
        for j, topic in enumerate(topics):
            ordered.append(((j + 0.5) / len(topics), cluster, topic))

    ordered.sort(key=lambda x: x[0])  # 정렬은 안정적이라 같은 위치면 CLUSTERS 순서가 유지된다
    return [{"topic": topic, "cluster": cluster} for _, cluster, topic in ordered]


def build_calendar(topics_per_cluster: int = 5) -> list[dict]:
    """큐를 처음부터 새로 만든다 (기존 큐는 무시) — 수동 실행용."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("환경변수 GEMINI_API_KEY가 설정되어 있지 않습니다.")
    client = genai.Client(api_key=api_key)
    return _round_robin_queue(client, topics_per_cluster, _existing_topics())


# 하루 2편(daily_auto_run.py의 PUBLISH_SLOTS) 체제에서 큐가 며칠 안에 바닥나는 걸 막기 위해,
# pop_next()가 큐를 꺼낼 때마다 이 밑으로 남았는지 확인해서 사람 개입 없이 자동으로 보충한다.
LOW_QUEUE_THRESHOLD = 10
REFILL_TOPICS_PER_CLUSTER = 3  # 클러스터 6개 x 3 (+한식 밥상 해부는 2배) = 21개씩 보충


def refill_if_low(
    queue: list[dict] | None = None,
    threshold: int = LOW_QUEUE_THRESHOLD,
    topics_per_cluster: int = REFILL_TOPICS_PER_CLUSTER,
) -> int:
    """큐가 threshold개 이하로 남으면 클러스터당 topics_per_cluster개(기본 20개)를 새로
    브레인스토밍해서 큐 뒤에 이어붙여 저장한다. 반환값: 새로 추가된 주제 개수(0이면 미보충)."""
    if queue is None:
        queue = load_calendar()
    if len(queue) > threshold:
        return 0

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY가 없어 콘텐츠 캘린더 큐 자동 보충을 건너뜁니다.")
        return 0
    client = genai.Client(api_key=api_key)

    # 이미 만든 영상뿐 아니라 큐에 아직 대기 중인 주제와도 겹치지 않게 한다.
    avoid = _existing_topics() + [item["topic"] for item in queue]
    new_items = _round_robin_queue(client, topics_per_cluster, avoid)
    save_calendar(queue + new_items)
    print(f"📅 콘텐츠 캘린더 큐가 {threshold}개 이하로 줄어 {len(new_items)}개를 자동으로 더 채웠습니다.")
    return len(new_items)


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

    try:
        refill_if_low(queue)
    except Exception as e:
        # 큐 보충 실패는 오늘 영상 생성 자체를 막을 이유가 없다 — 로그만 남기고 넘어간다.
        print(f"⚠️ 콘텐츠 캘린더 큐 자동 보충 중 오류(오늘 영상 생성에는 영향 없음): {e}")

    return today, upcoming


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"클러스터 {len(CLUSTERS)}개 x {count}개씩(가중치 적용) 주제 브레인스토밍 중...")
    new_queue = build_calendar(topics_per_cluster=count)
    save_calendar(new_queue)
    print(f"완료: {len(new_queue)}개 주제를 {CALENDAR_PATH}에 저장했습니다.\n")
    for i, item in enumerate(new_queue, 1):
        print(f"{i}. [{item['cluster']}] {item['topic']}")
