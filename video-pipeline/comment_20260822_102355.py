"""업로드 직후 자동 댓글이 403으로 실패해서(유튜브 쪽 처리 지연 추정) 재시도한다."""

from pipeline import build_pinned_comment
from youtube_upload import get_authenticated_service, insert_comment

VIDEO_ID = "PL1vhXMhEv4"
SOURCE = "Diabetes Care, Mayo Clinic, PubMed 메타분석, 삼성서울병원 건강정보"
NEXT_TOPIC_HINT = "카페인 섭취와 수면의 관계"

comment_text = build_pinned_comment(SOURCE, NEXT_TOPIC_HINT)
youtube = get_authenticated_service(credentials_file="credentials.json")
comment_id = insert_comment(youtube, VIDEO_ID, comment_text)
print("comment_id:", comment_id)
