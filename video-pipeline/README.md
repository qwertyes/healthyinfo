# video-pipeline

건강정보 숏폼 자동화 파이프라인. `my-video-creator`(단어장/코인뉴스 채널)의 구조를 재사용하되,
건강 니치에 맞게 간결화하고 컴플라이언스 가드레일을 넣었습니다. 근거: [PLAN.md](../PLAN.md) Phase 2.

## 지금 바로 되는 것 (계정 불필요, 테스트 완료)

- **`tts.py`** — Edge TTS로 한국어 여성(`ko-KR-SunHiNeural`)/남성(`ko-KR-InJoonNeural`) 내레이션 생성.
  API 키 없이 동작. `python tts.py`로 직접 실행하면 `samples/sample_female.mp3` 생성됨 (검증됨).
- **`script_prompt.py`** — 대본 생성용 시스템 프롬프트 + JSON 출력 스키마.
  `COMPLIANCE_COPY_GUIDE.md`의 금지 표현/필수 고지 규칙이 프롬프트에 고정 삽입되어 있음.

## 계정/키가 있어야 되는 것

- **`script_prompt.py`의 `generate_script()`** — 실제 LLM 호출부. 지금은 `NotImplementedError`를
  던지도록 되어 있음. 웹(`web/src/app/api/meal-plan/route.ts`)과 동일하게 Gemini(`GEMINI_API_KEY`,
  my-video-creator와 동일 키)를 직접 호출하도록 구현 예정.

## 완료된 것 (채널/인증)

- **YouTube 채널**: "한끼정답" (계정 silvernatural2@gmail.com, VocaMate `@KoreaNo1.`과 별도)
- **Google Cloud 프로젝트**: `hankki-video`, YouTube Data API v3 활성화됨
- **OAuth 클라이언트**: 데스크톱 앱 타입, `client_secret.json`으로 로컬에 저장(gitignore 처리)
- **`credentials.json`**: `generate_credentials.py`로 1회 인증 완료, `youtube.upload` +
  `youtube.force-ssl` 스코프 보유. `get_authenticated_service()`로 채널 정보 조회까지 테스트 완료.
- OAuth 앱은 아직 **"테스트" 상태** — silvernatural2@gmail.com이 테스트 사용자로 등록되어 있어
  본인 계정으로는 계속 사용 가능. 채널 소유자가 아닌 다른 사람이 관리자로 필요해지면 그때
  테스트 사용자를 추가하거나 앱을 정식 게시해야 함.

## 아직 만들지 않은 것

- 영상 합성(자막/배경/효과음 조립) — `my-video-creator/english_words_short.py`는 "10단어 플래시카드"
  포맷에 특화되어 있어 그대로 재사용하기보다, 건강 팁 60초 포맷(후킹 → 핵심 정보 → 고지 문구)에 맞는
  새 템플릿이 필요합니다. 비주얼 스타일(배경, 폰트, 자막 디자인)을 정하고 나서 작업하는 게 효율적이라
  후순위로 남겨뒀습니다.
- 사람 검수 단계의 실제 워크플로(현재는 프로세스만 `PLAN.md`에 정의됨, 툴링은 미구현)

## 남은 실행 순서

1. `script_prompt.generate_script()`에 Gemini 호출 구현
2. 영상 합성 템플릿 작성 (자막/배경/효과음)
3. `youtube_upload.upload_video()`로 첫 테스트 업로드 (`credentials.json`은 이미 준비됨)
