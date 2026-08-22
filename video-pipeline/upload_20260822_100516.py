"""pipeline.py로 만든 '카페인/혈당' 영상을 비공개로 업로드한다."""

from youtube_upload import upload_video

TITLE = "커피 마시면 혈당 오를까? 의외의 반전!"
DESCRIPTION = """커피 마시면 혈당이 튄다는 말, 들어보셨나요? 사실 절반은 맞고 절반은 틀린 이야기입니다. 학술지 'Diabetes Care'에 따르면, 식사 전 카페인 섭취는 일시적으로 인슐린 감수성을 14에서 최대 37퍼센트까지 낮추고 혈당 농도를 28퍼센트까지 높일 수 있습니다. 하지만 반전은 장기적인 결과에 있습니다. 매일 블랙커피를 2잔 정도 꾸준히 마시는 경우, 항산화 성분인 클로로겐산이 작용해 오히려 인슐린 저항성을 개선한다는 연구 결과가 있죠. 핵심은 '설탕과 시럽'을 뺀 블랙커피여야 한다는 점, 그리고 아침에 섭취하는 것이 대사 건강에 더 유리할 수 있다는 점입니다.

이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다.

출처: Diabetes Care, 한국인 대상 역학 연구

#카페인 #혈당관리 #커피 #당뇨예방 #건강상식 #한끼정답"""

TAGS = ["카페인", "혈당관리", "커피", "당뇨예방", "건강상식", "한끼정답"]

result = upload_video(
    file_path="output/20260822_100516_short.mp4",
    title=TITLE,
    description=DESCRIPTION,
    tags=TAGS,
    privacy_status="private",
    credentials_file="credentials.json",
    category_id="27",  # 교육
)
print(result)
