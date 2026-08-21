"""
Pexels API로 영상 배경용 스톡 사진을 검색·다운로드한다.
무료 API, 상업적 유튜브 영상에도 라이선스 문제 없이 사용 가능 (Pexels License).
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def search_photo(query: str, out_path: str) -> str | None:
    """query로 세로(portrait) 사진 1장을 검색해 out_path에 저장한다."""
    paths = search_photos(query, out_path.rsplit(".", 1)[0], count=1)
    return paths[0] if paths else None


def search_photos(query: str, out_path_prefix: str, count: int = 3) -> list[str]:
    """
    query로 세로(portrait) 사진 여러 장을 검색해 out_path_prefix_0.jpg, _1.jpg ... 로 저장한다.
    영상 배경을 한 장짜리 정지 이미지가 아니라 여러 장으로 전환시키는 용도.
    """
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []

    try:
        response = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": api_key},
            params={"query": query, "per_page": count, "orientation": "portrait"},
            timeout=10,
        )
        response.raise_for_status()
        photos = response.json().get("photos", [])

        paths = []
        for i, photo in enumerate(photos[:count]):
            image_resp = requests.get(photo["src"]["portrait"], timeout=15)
            image_resp.raise_for_status()
            path = f"{out_path_prefix}_{i}.jpg"
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "wb") as f:
                f.write(image_resp.content)
            paths.append(path)
        return paths
    except requests.RequestException:
        return []


if __name__ == "__main__":
    paths = search_photos("grilled chicken breast", "video-pipeline/samples/stock_multi", count=3)
    print(f"결과: {paths}")
