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
  던지도록 되어 있음. Vercel AI Gateway API 키가 준비되면 이 함수 안에서 모델을 호출하도록 구현.
- **`youtube_upload.py`** (`my-video-creator/youtube_api.py`를 그대로 복사, 이미 범용적으로 작성되어
  있어 수정 없이 재사용 가능) — 업로드하려면 **HealthyInfo 전용 YouTube 채널**을 새로 만들고,
  그 채널에 대한 Google Cloud OAuth 클라이언트(`client_secrets.json`)를 발급받아
  `generate_credentials_locally()`로 `credentials.json`을 1회 생성해야 함.
  **주의**: 기존 VocaMate(`@KoreaNo1.`) 채널의 `credentials.json`을 재사용하면 안 됨 — 다른 채널.

## 아직 만들지 않은 것

- 영상 합성(자막/배경/효과음 조립) — `my-video-creator/english_words_short.py`는 "10단어 플래시카드"
  포맷에 특화되어 있어 그대로 재사용하기보다, 건강 팁 60초 포맷(후킹 → 핵심 정보 → 고지 문구)에 맞는
  새 템플릿이 필요합니다. 비주얼 스타일(배경, 폰트, 자막 디자인)을 정하고 나서 작업하는 게 효율적이라
  후순위로 남겨뒀습니다.
- 사람 검수 단계의 실제 워크플로(현재는 프로세스만 `PLAN.md`에 정의됨, 툴링은 미구현)

## 실행 순서 (계정 준비 후)

1. `pip install -r requirements.txt`
2. Google Cloud Console에서 새 프로젝트 생성 → YouTube Data API v3 활성화 → OAuth 클라이언트(데스크톱 앱) 발급
3. `youtube_upload.generate_credentials_locally(client_secrets_file, "credentials.json")` 1회 실행 (브라우저 인증)
4. `script_prompt.generate_script()`에 LLM 호출 구현
5. 영상 합성 템플릿 작성 후 `youtube_upload.upload_video()`로 업로드
