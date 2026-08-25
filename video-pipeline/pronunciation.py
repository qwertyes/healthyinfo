"""
TTS가 잘못 읽는 단어를 발음대로 치환해서 내레이션 입력 텍스트에만 적용한다.
대본 원문(result.script, 웹 아티클/영상 설명란에 쓰이는 값)은 건드리지 않는다 —
"오메가3"처럼 쓰기엔 이 표기가 맞고, 소리 낼 때만 "오메가쓰리"로 바꾸면 되기 때문.
카라오케 자막도 화면엔 원문 표기("오메가3")가 나오도록, TTS가 돌려준 단어 타이밍의
텍스트만 restore_original_spelling()으로 다시 원문 표기로 되돌려서 쓴다(타이밍 자체는
그대로 유지) — 들을 땐 "오메가쓰리", 볼 땐 "오메가3".

건강/영양 콘텐츠에서 한국어 TTS가 자주 틀리는 패턴: 알파벳+숫자 조합을 숫자 그대로
(사이시옷 없이) 읽어버리는 경우가 많다 — "오메가3"를 "오메가삼"으로, "비타민B12"를
"비타민비십이"가 아니라 이상하게 끊어 읽는 식. 실제로 만든 영상에서 이상하게 들리는
단어를 발견하면 이 목록에 계속 추가하면 된다.
"""

# (원문 표기, TTS용 발음 표기) — 원문이 더 긴 것부터 순서대로 적용해야 부분 겹침을
# 방지할 수 있으므로, apply_pronunciation_fixes()가 이 순서를 그대로 사용한다.
PRONUNCIATION_FIXES: list[tuple[str, str]] = [
    # 오메가 지방산 — 사용자가 실제로 "오메가삼"으로 잘못 읽히는 걸 확인한 케이스
    ("오메가3", "오메가쓰리"),
    ("오메가6", "오메가식스"),
    ("오메가9", "오메가나인"),
    # 비타민B12 — 채식/비건 식단 콘텐츠에서 자주 등장, "비타민비십이"로 읽혀야 함
    ("비타민B12", "비타민비십이"),
    ("비타민B6", "비타민비식스"),
    # 혈당지수(GI) — 영문 약자를 알파벳 그대로 읽어야 하는데 안 읽히는 경우 대비
    ("GI지수", "지아이지수"),
    ("BMI", "비엠아이"),
    ("HDL", "에이치디엘"),
    ("LDL", "엘디엘"),
]


def apply_pronunciation_fixes(text: str) -> str:
    """TTS로 보내기 직전에만 호출한다 — 반환값을 result.script에 다시 대입하지 말 것."""
    for original, spoken in PRONUNCIATION_FIXES:
        text = text.replace(original, spoken)
    return text


def restore_original_spelling(text: str) -> str:
    """TTS가 돌려준 단어 타이밍의 텍스트를 자막용으로 원문 표기로 되돌린다."""
    for original, spoken in PRONUNCIATION_FIXES:
        text = text.replace(spoken, original)
    return text
