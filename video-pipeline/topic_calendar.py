"""
클러스터별로 영상 주제를 여러 개 미리 브레인스토밍해서 큐로 쌓아두는 모듈.

기존 방식(영상 하나 만들 때마다 그 대본이 예고한 주제 하나만 다음 실행에 이어받는 체인,
pipeline.py의 옛 content_queue.json)은 "영상을 만들면서 그때그때 다음 제목이 정해지는" 구조라
진짜 사전 기획이 아니라는 피드백을 받았다. 이 모듈은 CLUSTERS(한식 밥상 해부 / 편의점·배달 한끼 / 조리·보관의 과학 /
시즌·상황별 한끼 / 음료·간식 — 소재 기준 5개, FORMAT_CLUSTERS 참고 / 미신 팩트체크 / 상황 따라가기 /
체감형 환산 / 현장 체크리스트 / 음식 궁합 속설 검증 — 이야기 구조 기준 5개) 각각에서 주제를 여러 개
한 번에 뽑아 비중에 맞게 섞은 큐를 content_calendar.json에 저장해둔다.
pipeline.py는 인자 없이 실행되면 이 큐에서 하나씩 꺼내 쓴다.

주제 브레인스토밍은 사실 검증이 필요 없는 단계라 검색 그라운딩 없이 순수 생성만 한다.
실제 대본 작성(script_prompt.generate_script)은 여전히 검색 그라운딩 + 컴플라이언스 검증을
거친다 — 이 모듈은 "무엇을 다룰지"만 미리 정할 뿐, "어떻게 쓸지"는 매번 새로 검증한다.

실행: python topic_calendar.py [클러스터당_주제_개수(기본 5)]
"""

import json
import os
import sys

import numpy as np

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
# "성분표 읽기"는 이후 영상 내용이 시청자에게 너무 어렵다는 피드백으로 다시 빼서 5개로 줄였다.
#
# 그런데 소재(한식/편의점/조리법/...)만 바꿔도 거의 모든 주제가 "A를 이렇게 vs 저렇게 하면
# 영양소가 얼마나 보존/손실/변하는가" 라는 같은 이야기 구조로 나온다는 피드백을 받았다. 그래서
# 아래 5개는 소재가 아니라 "이야기 구조(패턴)"로 나눈 클러스터 — 비교형 틀에서 벗어나게 한다.
FORMAT_CLUSTERS = ["미신 팩트체크", "상황 따라가기", "체감형 환산", "현장 체크리스트", "음식 궁합 속설 검증"]
# 식사 관련 주제만으로는 영상이 비슷하게 반복된다는 피드백으로, 음식 밖의 건강 상식(약 복용·질병
# 오해·생활 습관)을 섞기 위해 추가한 클러스터.
# "몸이 보내는 신호"는 "몸에 이런 현상이 있으면 이걸 의심해봐라" 류 영상을 원한다는 피드백으로 추가
# (2026-11-06). 병 관련 다룰 거리가 많으니 건강 비중을 늘리자는 방향이라 기존 클러스터 비중은 그대로 둔다.
HEALTH_CLUSTERS = ["약 복용 상식", "질병 오해 바로잡기", "생활 건강 상식", "몸이 보내는 신호"]
CLUSTERS = ["한식 밥상 해부", "편의점·배달 한끼", "조리·보관의 과학", "시즌·상황별 한끼", "음료·간식"] + FORMAT_CLUSTERS + HEALTH_CLUSTERS

# 큐에서 차지하는 비중 — 채널에 가장 잘 맞는 "한식 밥상 해부"와, 음식 주제 사이에 충분히 섞이도록
# 건강 상식 클러스터를 다른 클러스터의 2배로 뽑는다 (건강 상식이 큐의 약 1/3).
CLUSTER_WEIGHTS = {"한식 밥상 해부": 2, **{c: 2 for c in HEALTH_CLUSTERS}}

_CLUSTER_HINTS = {
    "한식 밥상 해부": "김치·된장·국물·나물·밥·반찬처럼 매일 먹는 한식 한 가지를 골라 영양·나트륨·먹는 방법을 해부하는 주제 (예: 김치찌개 국물, 된장국 건더기, 라면 국물 vs 곰탕 국물)",
    "편의점·배달 한끼": "삼각김밥·김밥·샌드위치·국밥·치킨처럼 편의점·배달 한 끼를 종류별로 비교하고 고르는 법 (특정 브랜드·제품명은 금지)",
    "조리·보관의 과학": "삶기·찌기·굽기·튀기기, 에어프라이어, 튀김 기름 재사용, 냉동 vs 신선, 통조림처럼 같은 재료를 어떻게 다루느냐에 따른 차이",
    "시즌·상황별 한끼": "가을 제철 식재료, 명절 음식 후 속, 야근 후 야식, 해장국처럼 시기·상황에 맞는 한 끼 이야기",
    "미신 팩트체크": "'~카더라'식 건강·식습관 속설을 하나 골라 사실인지 검증하는 주제. 'A vs B 비교'가 아니라 명제 하나를 긍정/부정으로 판정하는 구조여야 함 (예: 매운 음식 먹으면 위벽이 헐어 위암 위험이 커진다?, 잠을 못 자면 다음 날 폭식한다는 말이 진짜일까?)",
    "상황 따라가기": "재료나 성분이 아니라 특정 생활 상황·인물의 식사 장면을 따라가며 문제를 짚는 주제. 비교형이 아니라 하나의 장면·타임라인을 그려야 함 (예: 야근 끝나고 11시에 집에 온 직장인의 식탁, 뭐가 문제일까?, 아침을 거르고 커피만 마신 하루, 몸에서 무슨 일이 벌어질까?)",
    "체감형 환산": "수치를 밥숟가락·각설탕·종이컵처럼 익숙한 단위로 환산해서 몸으로 체감시키는 주제 (예: 라면 한 봉지 나트륨, 밥숟가락으로 치면 몇 숟갈일까?, 콜라 한 캔 당분, 각설탕으로 쌓으면 몇 개일까?)",
    "현장 체크리스트": "비교·분석이 아니라 장보기·외식 현장에서 바로 쓸 수 있는 선택 기준 한 가지를 짧게 알려주는 주제 (예: 두유 고를 때 뒷면에서 이 숫자 하나만 보세요, 계란 고를 때 날짜보다 먼저 봐야 할 것은?)",
    "음식 궁합 속설 검증": "두 음식을 함께 먹었을 때의 궁합 속설(같이 먹으면 좋다/나쁘다)을 검증하는 주제 (예: 시금치와 두부를 같이 먹으면 정말 결석이 생길까?, 우유와 함께 먹으면 안 된다는 음식들, 진짜일까?)",
    "음료·간식": "제로 음료·감미료, 에너지드링크 카페인, 커피, 소금 종류, 과자·견과·프로틴바처럼 매일 사 먹는 음료와 간식",
    "약 복용 상식": "감기약·진통제·소화제처럼 흔한 약을 먹을 때 누구나 궁금한 일반 상식 (예: 약을 우유나 커피로 먹어도 될까?, 식후 30분은 꼭 지켜야 할까?, 유통기한 지난 약 먹어도 될까?). 특정 약 이름·복용량 지시나 약을 끊고 바꾸는 판단처럼 개인 의료 판단이 필요한 주제는 금지",
    "질병 오해 바로잡기": "감기·위염·고혈압·허리 통증처럼 흔한 질병·증상에 대해 널리 퍼진 오해 하나를 바로잡는 주제 (예: 감기는 찬 바람을 맞아서 걸린다?, 혈압약은 한번 먹으면 평생 끊을 수 없다?, 코피 날 때 고개를 뒤로 젖혀야 한다?). 치료법 안내가 아니라 오해와 사실을 구분하는 구조",
    "몸이 보내는 신호": "손발 저림·눈 밑 떨림·잦은 멍·입냄새·소변 색 변화·손톱 모양처럼 누구나 겪는 몸의 작은 변화 하나를 골라, 흔하고 걱정 없는 원인과 병원에서 확인해봐야 하는 신호를 구분해주는 주제 (예: 자고 일어나면 손이 붓는다면? 이런 경우엔 확인이 필요합니다, 자꾸 다리에 쥐가 나는 이유, 단순 피로일까?, 소변에 거품이 많으면 콩팥 문제일까?). '이 증상이면 OO병'처럼 진단을 단정하는 주제나 암·중증 질환을 겁주는 주제는 금지",
    "생활 건강 상식": "수면·자세·스트레칭·눈 건강·손 씻기·운동처럼 음식 밖의 생활 습관에 관한 궁금증 (예: 낮잠은 몇 분이 가장 좋을까?, 하루 만 보 걷기는 꼭 지켜야 할까?, 스마트폰 블루라이트가 정말 눈을 망칠까?)",
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
- 약·질병 주제도 의학 용어 위주의 어려운 주제는 피하고, 누구나 한 번쯤 들어본 일상적인 궁금증으로
  쓰세요. 특정 약의 복용량이나 약을 끊고 바꾸는 판단처럼 개인 진료가 필요한 주제는 금지입니다.
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


# ── 중복 주제 검사 ─────────────────────────────────────────────────────────────
# 프롬프트에 "이미 다룬 주제" 목록을 넘겨도 flash-lite 모델이 표현만 바꾼 같은 주제를 계속 낸다
# (2026-11-06 자동 보충분 54개 중 22개가 지난 영상과 중복). 그래서 생성 후 코드로 한 번 더 거른다.
# 임베딩 유사도만으로는 0.85~0.92 구간에서 중복과 단순히 소재만 비슷한 주제가 섞여서(실측),
# 확실한 구간만 바로 판정하고 애매한 구간은 모델에게 "같은 내용인지" 따로 판정시킨다.
EMBED_MODEL = "gemini-embedding-001"
# 판정은 flash-lite로 하면 프롬프트 예시와 똑같은 쌍(감기 찬 바람 vs 젖은 머리)도 놓쳐서 한 단계 위 모델을 쓴다.
# 클러스터당 1회 호출이라 비용 부담은 작다.
DUP_JUDGE_MODEL = "gemini-flash-latest"
DUP_SURE_THRESHOLD = 0.92   # 이 이상이면 판정 없이 중복으로 버림
DUP_CHECK_THRESHOLD = 0.84  # 이 이상~SURE 미만은 모델 판정, 미만은 새 주제로 통과
DUP_NEIGHBORS = 5

DUP_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"duplicate_indices": {"type": "array", "items": {"type": "integer"}}},
    "required": ["duplicate_indices"],
}

DUP_JUDGE_PROMPT = """유튜브 건강 숏폼 채널의 새 주제 후보가 이미 만든 영상과 사실상 같은 내용인지 판정하세요.
각 후보 아래에 가장 비슷한 기존 영상 제목들이 있습니다.

중복으로 보는 경우: 시청자가 보고 "이거 전에 본 얘긴데"라고 느낄 만큼 핵심 질문이나 답이 같은 것.
표현만 바꾼 것, 같은 속설·같은 행동을 다른 각도로 묻는 것도 중복입니다.
(예: "약은 꼭 식후 30분?" ≈ "식후 30분 꼭 지켜야 할까?", "서방정 쪼개 먹으면 안 되는 이유" ≈ "알약 쪼개 먹어도 될까?",
"감기는 찬 바람 때문?" ≈ "감기는 젖은 머리 탓?")
중복이 아닌 경우: 소재(나트륨, 커피, 약 등)만 겹치고 묻는 질문이 다른 것.
(예: "진통제 자주 먹으면 내성이 생길까?" vs "유통기한 지난 약 먹어도 될까?"는 중복 아님)

같은 음식·약·행동을 다루면서 관심사(나트륨, 당·혈당, 영양소 손실, 복용법 등)까지 같으면 질문 각도가
조금 달라도 중복입니다. (예: "된장찌개 건더기·국물 나트륨" ≈ "된장찌개 국물 다 마시면 나트륨",
"만 보 띄엄띄엄 걸어도 될까" ≈ "하루 만 보 꼭 채워야 할까", "식은 밥 데워 먹으면 혈당" ≈ "뜨거운 밥 vs 식힌 밥 혈당")
버린 후보는 새 주제로 다시 뽑으므로, 확신이 없으면 중복으로 판정하세요.

중복인 후보의 번호만 duplicate_indices에 담으세요."""


def _embed(client: genai.Client, texts: list[str]) -> np.ndarray:
    vectors = []
    for i in range(0, len(texts), 100):
        resp = client.models.embed_content(
            model=EMBED_MODEL,
            contents=texts[i : i + 100],
            config=genai_types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
        )
        vectors.extend(e.values for e in resp.embeddings)
    arr = np.array(vectors, dtype=float)
    return arr / np.linalg.norm(arr, axis=1, keepdims=True)


class DuplicateFilter:
    """기존 영상·대기 큐·이번에 새로 받은 주제와 겹치는 후보를 걸러낸다. 받아들인 주제는 계속 누적해서
    다른 클러스터의 후보끼리도 겹치지 않게 한다. 임베딩/판정 호출이 실패하면 걸러내지 않고 통과시킨다 —
    큐 보충 자체가 멈추는 것보다 중복 몇 개가 섞이는 게 낫다."""

    def __init__(self, client: genai.Client, known: list[str]):
        self.client = client
        self.known = list(dict.fromkeys(known))
        self.vectors = _embed(client, self.known) if self.known else np.zeros((0, 1))

    def _judge(self, items: list[tuple[str, list[str]]]) -> set[int]:
        lines = []
        for i, (cand, neighbors) in enumerate(items):
            lines.append(f"[{i}] 후보: {cand}")
            lines.extend(f"    - 기존: {n}" for n in neighbors)
        response = self.client.models.generate_content(
            model=DUP_JUDGE_MODEL,
            contents="\n".join(lines),
            config=genai_types.GenerateContentConfig(
                system_instruction=DUP_JUDGE_PROMPT,
                response_mime_type="application/json",
                response_json_schema=DUP_JUDGE_SCHEMA,
                temperature=0.0,
            ),
        )
        return set(json.loads(response.text)["duplicate_indices"])

    def filter(self, candidates: list[str]) -> tuple[list[str], list[str]]:
        """반환: (통과한 주제, 중복으로 버린 주제)."""
        if not candidates:
            return [], []
        try:
            cand_vecs = _embed(self.client, candidates)
        except Exception as e:
            print(f"⚠️ 중복 검사 임베딩 실패 — 검사 없이 통과시킵니다: {e}")
            self.known += candidates
            return candidates, []

        accepted: list[str] = []
        accepted_vecs: list[np.ndarray] = []
        dropped: list[str] = []
        to_judge: list[tuple[int, list[str]]] = []
        for i, (cand, vec) in enumerate(zip(candidates, cand_vecs)):
            pool_texts = self.known + accepted
            if not pool_texts:
                accepted.append(cand); accepted_vecs.append(vec); continue
            pool_vecs = np.vstack([v for v in (self.vectors, *accepted_vecs) if len(v)])
            sims = pool_vecs @ vec
            top = np.argsort(-sims)[:DUP_NEIGHBORS]
            best = float(sims[top[0]])
            if best >= DUP_SURE_THRESHOLD:
                dropped.append(cand)
                print(f"   🔁 중복 제외({best:.2f}): {cand}  ≈  {pool_texts[top[0]]}")
            elif best >= DUP_CHECK_THRESHOLD:
                to_judge.append((i, [pool_texts[j] for j in top]))
            else:
                accepted.append(cand); accepted_vecs.append(vec)

        if to_judge:
            try:
                dup_idx = self._judge([(candidates[i], nb) for i, nb in to_judge])
            except Exception as e:
                print(f"⚠️ 중복 판정 호출 실패 — 애매한 후보는 통과시킵니다: {e}")
                dup_idx = set()
            for k, (i, neighbors) in enumerate(to_judge):
                if k in dup_idx:
                    dropped.append(candidates[i])
                    print(f"   🔁 중복 제외(판정): {candidates[i]}  ≈  {neighbors[0]}")
                else:
                    accepted.append(candidates[i]); accepted_vecs.append(cand_vecs[i])

        if accepted:
            self.known += accepted
            new_vecs = np.vstack(accepted_vecs)
            self.vectors = new_vecs if len(self.vectors) == 0 else np.vstack([self.vectors, new_vecs])
        return accepted, dropped


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


MAX_TOPIC_ROUNDS = 3  # 중복으로 버려진 만큼 다시 뽑는 최대 횟수(첫 생성 포함)


def _round_robin_queue(client: genai.Client, topics_per_cluster: int, avoid: list[str]) -> list[dict]:
    """클러스터마다 topics_per_cluster개(CLUSTER_WEIGHTS가 있으면 그 배수)씩 뽑아, 한 클러스터
    주제로 몰리지 않게 비중에 비례해서 고르게 섞은 큐를 만든다. 뽑은 주제는 DuplicateFilter로
    기존 영상·대기 큐와 겹치는지 검사하고, 버려진 만큼 다시 뽑는다(최대 MAX_TOPIC_ROUNDS회)."""
    dup_filter = DuplicateFilter(client, avoid)
    ordered = []  # (큐 안에서의 상대 위치, 클러스터, 주제)
    for cluster in CLUSTERS:
        count = topics_per_cluster * CLUSTER_WEIGHTS.get(cluster, 1)
        topics: list[str] = []
        for _ in range(MAX_TOPIC_ROUNDS):
            need = count - len(topics)
            if need <= 0:
                break
            candidates = generate_topics_for_cluster(client, cluster, need, avoid)
            accepted, dropped = dup_filter.filter(candidates)
            topics += accepted
            avoid = avoid + candidates  # 버린 후보도 다시 내지 않게 피할 목록에 넣는다
        if len(topics) < count:
            print(f"   ⚠️ [{cluster}] 중복을 빼고 나니 {len(topics)}/{count}개만 확보")
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
REFILL_TOPICS_PER_CLUSTER = 3  # 클러스터 14개 x 3 (+가중치 2배 5개) = 57개씩 보충


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
