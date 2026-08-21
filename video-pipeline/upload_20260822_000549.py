"""pipeline.py로 만든 '공복 커피' 영상을 비공개로 업로드한다."""

from youtube_upload import upload_video

TITLE = "공복 커피, 마셔도 될까? 의외의 사실"
DESCRIPTION = """아침 공복에 마시는 커피 한 잔, 위장 망친다는 말 사실일까요? 결론부터 말씀드리면 대부분의 건강한 성인에게는 큰 문제가 없습니다. 미국 소화기학회 전문가들에 따르면 우리 위는 두꺼운 점액층으로 스스로를 보호하기 때문에 커피가 위벽에 직접적인 손상을 주지는 않습니다. 8천 명 이상을 대상으로 한 연구에서도 커피 섭취와 위궤양 간의 유의미한 연관성은 발견되지 않았죠. 다만, 역류성 식도염이나 위염이 있다면 주의가 필요합니다. 공복에는 카페인이 더 빠르게 흡수되어 속쓰림이나 불안감을 유발할 수 있기 때문입니다. 특히 65도 이상의 뜨거운 커피는 식도 점막을 손상시킬 수 있으니 온도도 꼭 확인하세요.

이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다.

출처: 미국 소화기학회(AGA), 국제암연구소(IARC)

#공복커피 #커피건강 #아침루틴 #위건강 #카페인 #한끼정답"""

TAGS = ["공복커피", "커피건강", "아침루틴", "위건강", "카페인", "한끼정답"]

result = upload_video(
    file_path="output/20260822_000549_short.mp4",
    title=TITLE,
    description=DESCRIPTION,
    tags=TAGS,
    privacy_status="private",
    credentials_file="credentials.json",
    category_id="27",  # 교육
)
print(result)
