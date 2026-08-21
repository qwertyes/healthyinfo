"""1회성 테스트 업로드 스크립트 — pipeline.py로 만든 영상을 비공개로 올려 업로드 흐름을 검증한다."""

from youtube_upload import upload_video

TITLE = "간헐적 단식, 누구나 해도 괜찮을까요?"
DESCRIPTION = """혹시 요즘 유행하는 간헐적 단식, 아무나 시작해도 될까요? 단순히 굶는 것이 아니라 시간 제한을 두는 이 방식은 체중 관리의 방법 중 하나로 주목받고 있습니다. 미국 의학협회 저널(JAMA)에 게재된 연구에 따르면, 정해진 시간 동안만 식사하는 방식이 에너지 섭취를 조절하는 데 도움을 줄 수 있다고 알려져 있습니다. 다만, 성장기 청소년이나 임산부, 특정 영양 관리가 필요한 분들에게는 오히려 무리가 될 수 있다는 의견이 많습니다. 개인의 건강 상태에 따라 필요한 영양 섭취가 달라질 수 있으므로 무리한 단식보다는 본인의 라이프스타일에 맞춘 균형 잡힌 식단이 중요합니다. 이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다.

출처: 미국 의학협회 저널(JAMA)

#간헐적단식 #식단관리 #건강상식 #한끼정답 #영양정보"""

TAGS = ["간헐적단식", "식단관리", "건강상식", "한끼정답", "영양정보"]

result = upload_video(
    file_path="output/20260821_192258_short.mp4",
    title=TITLE,
    description=DESCRIPTION,
    tags=TAGS,
    privacy_status="private",
    credentials_file="credentials.json",
    category_id="27",  # 교육
)
print(result)
