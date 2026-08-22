"""private 상태 영상에 바로 댓글을 달면 403이 나는 문제 우회.
english_words_short.py가 쓰는 패턴과 동일: 잠깐 unlisted로 전환 -> 댓글 등록 -> 다시 private로 전환."""

import time

from pipeline import build_pinned_comment
from youtube_upload import get_authenticated_service, insert_comment

VIDEO_ID = "PL1vhXMhEv4"
SOURCE = "Diabetes Care, Mayo Clinic, PubMed 메타분석, 삼성서울병원 건강정보"
NEXT_TOPIC_HINT = "카페인 섭취와 수면의 관계"

youtube = get_authenticated_service(credentials_file="credentials.json")

print("1) unlisted로 전환...")
youtube.videos().update(
    part="status",
    body={"id": VIDEO_ID, "status": {"privacyStatus": "unlisted"}},
).execute()

print("2) 유튜브 처리 대기 (15초)...")
time.sleep(15)

print("3) 댓글 등록 시도...")
comment_text = build_pinned_comment(SOURCE, NEXT_TOPIC_HINT)
comment_id = insert_comment(youtube, VIDEO_ID, comment_text)
print("comment_id:", comment_id)

print("4) 다시 private로 전환...")
youtube.videos().update(
    part="status",
    body={"id": VIDEO_ID, "status": {"privacyStatus": "private"}},
).execute()

print("완료.")
