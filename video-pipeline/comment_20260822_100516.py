"""이미 업로드된 카페인/혈당 영상(video_id: oaiPJejRkNI)에 고정 댓글을 등록한다."""

from pipeline import build_pinned_comment
from youtube_upload import get_authenticated_service, insert_comment

VIDEO_ID = "oaiPJejRkNI"
SOURCE = "Diabetes Care, 한국인 대상 역학 연구"
NEXT_TOPIC_HINT = "혈당을 올리는 숨겨진 당류"

comment_text = build_pinned_comment(SOURCE, NEXT_TOPIC_HINT)
youtube = get_authenticated_service(credentials_file="credentials.json")
comment_id = insert_comment(youtube, VIDEO_ID, comment_text)
print("comment_id:", comment_id)
