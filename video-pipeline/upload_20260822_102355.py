"""pipeline.py로 재생성한 '카페인/혈당'(수치 검증 강화 버전) 영상을 비공개로 업로드하고,
고정 댓글도 upload_video()의 comment_text로 함께 자동 등록한다 (앞으로의 표준 패턴)."""

from pipeline import build_pinned_comment
from youtube_upload import upload_video

TITLE = "커피 마시면 혈당이 오른다고요?"
SOURCE = "Diabetes Care, Mayo Clinic, PubMed 메타분석, 삼성서울병원 건강정보"
NEXT_TOPIC_HINT = "카페인 섭취와 수면의 관계"

DESCRIPTION = """커피를 마시면 혈당이 오를까, 아니면 도움이 될까? 결론부터 말하면 단기적 반응과 장기적 효과가 정반대입니다. 먼저 단기적으로는 카페인이 아드레날린 분비를 촉진해 간에 저장된 당을 혈액으로 내보내는데요. 당뇨병 환자를 대상으로 한 연구에서는 200~500mg의 카페인 섭취 시 식후 혈당 농도가 최대 28%까지 증가할 수 있음이 확인되었습니다. 식후 직후의 고용량 카페인은 인슐린 민감도를 15% 이상 떨어뜨릴 수 있어 주의가 필요하죠. 하지만 장기적으로는 다릅니다. 커피 속 클로로겐산 성분은 오히려 인슐린 저항성 개선을 돕는데요. 실제로 하루 커피 1잔을 더 마실 때마다 제2형 당뇨병 위험이 6~9% 낮아진다는 연구 결과도 있습니다. 핵심은 설탕과 시럽을 뺀 블랙커피를 마시는 것, 그리고 식후 바로 마시는 습관을 점검하는 것입니다.

이 정보는 일반적인 영양 정보이며, 의학적 진단·치료·처방을 대체하지 않습니다.

출처: {source}

#혈당관리 #커피효능 #카페인 #당뇨예방 #건강상식 #한끼정답""".format(source=SOURCE)

TAGS = ["혈당관리", "커피효능", "카페인", "당뇨예방", "건강상식", "한끼정답"]

comment_text = build_pinned_comment(SOURCE, NEXT_TOPIC_HINT)

result = upload_video(
    file_path="output/20260822_102355_short.mp4",
    title=TITLE,
    description=DESCRIPTION,
    tags=TAGS,
    privacy_status="private",
    credentials_file="credentials.json",
    category_id="27",  # 교육
    comment_text=comment_text,
)
print(result)
