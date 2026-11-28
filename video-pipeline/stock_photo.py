"""
Pexels API로 영상 배경용 스톡 사진을 검색·다운로드한다.
무료 API, 상업적 유튜브 영상에도 라이선스 문제 없이 사용 가능 (Pexels License).

장면별 배경(search_scene_photos): 대본이 장면마다 다른 대상을 말하는데 영상 전체를 검색어 하나로
찾은 사진 8장으로 채우면 말과 그림이 따로 논다는 피드백(2026-11-28)으로, 장면마다 따로 검색한다.
Pexels 검색 1순위가 항상 검색어와 맞지는 않아서, 후보 여러 장의 설명(alt)과 검색어 단어가 얼마나
겹치는지로 다시 골라 쓰고, 다른 장면에서 이미 쓴 사진은 건너뛴다.
"""

import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
CANDIDATES_PER_QUERY = 15

# 검색어 단어 중 사진 설명과 겹쳐도 의미 없는 말
_STOPWORDS = {"a", "an", "the", "of", "on", "in", "with", "and", "for", "to", "at", "korean", "food", "dish"}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", (text or "").lower())
    # 복수형 차이(noodle/noodles)는 같은 단어로 본다
    return {w.rstrip("s") for w in words if w not in _STOPWORDS and len(w) > 2}


def _search(api_key: str, query: str, per_page: int) -> list[dict]:
    try:
        response = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": api_key},
            params={"query": query, "per_page": per_page, "orientation": "portrait"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("photos", [])
    except requests.RequestException:
        return []


def _download(photo: dict, path: str) -> bool:
    try:
        image_resp = requests.get(photo["src"]["portrait"], timeout=15)
        image_resp.raise_for_status()
    except requests.RequestException:
        return False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(image_resp.content)
    return True


def _rank_by_relevance(photos: list[dict], query: str) -> list[dict]:
    """사진 설명(alt)에 검색어 단어가 많이 들어간 순으로 정렬한다. 동점이면 Pexels 원래 순위 유지."""
    q = _tokens(query)
    if not q:
        return photos
    return sorted(photos, key=lambda p: -len(q & _tokens(p.get("alt", ""))))


def _fallback_queries(query: str, general_query: str | None) -> list[str]:
    """장면 검색어로 못 찾으면 점점 넓혀서 다시 찾는다: 원래 검색어 → 앞 단어 하나 뺀 것 → 마지막 두 단어 → 대표 검색어."""
    words = query.split()
    chain = [query]
    if len(words) > 2:
        chain += [" ".join(words[1:]), " ".join(words[-2:])]
    if general_query:
        chain.append(general_query)
    return list(dict.fromkeys(q for q in chain if q.strip()))


def search_scene_photos(queries: list[str], out_path_prefix: str, general_query: str | None = None) -> list[str | None]:
    """
    장면 검색어마다 사진 1장씩 찾아 out_path_prefix_{i}.jpg로 저장한다 (i = 장면 번호).
    반환 리스트는 queries와 길이가 같고, 끝내 못 찾은 장면은 None.
    """
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return [None] * len(queries)

    used_ids: set[int] = set()
    results: list[str | None] = []
    for i, query in enumerate(queries):
        path = f"{out_path_prefix}_{i}.jpg"
        found = None
        for q in _fallback_queries(query, general_query):
            photos = [p for p in _search(api_key, q, CANDIDATES_PER_QUERY) if p.get("id") not in used_ids]
            for photo in _rank_by_relevance(photos, query):
                if _download(photo, path):
                    used_ids.add(photo.get("id"))
                    found = path
                    break
            if found:
                if q != query:
                    print(f"   (장면 {i + 1} '{query}' → 대체 검색어 '{q}'로 찾음)")
                break
        results.append(found)
    return results


def search_photo(query: str, out_path: str) -> str | None:
    """query로 세로(portrait) 사진 1장을 검색해 out_path에 저장한다."""
    paths = search_photos(query, out_path.rsplit(".", 1)[0], count=1)
    return paths[0] if paths else None


def search_photos(query: str, out_path_prefix: str, count: int = 3) -> list[str]:
    """
    query로 세로(portrait) 사진 여러 장을 검색해 out_path_prefix_0.jpg, _1.jpg ... 로 저장한다.
    장면 정보가 없을 때(옛 대본 등)의 대체 경로.
    """
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
    photos = _rank_by_relevance(_search(api_key, query, max(count, CANDIDATES_PER_QUERY)), query)
    paths = []
    for photo in photos:
        if len(paths) >= count:
            break
        path = f"{out_path_prefix}_{len(paths)}.jpg"
        if _download(photo, path):  # 장수가 많아진 만큼, 한 장 실패로 나머지까지 버리지 않는다
            paths.append(path)
    return paths


if __name__ == "__main__":
    paths = search_scene_photos(
        ["korean pork belly grill", "lettuce wrap ssam", "garlic cloves bowl"],
        "video-pipeline/samples/scene_test",
        general_query="korean table meal",
    )
    print(f"결과: {paths}")
