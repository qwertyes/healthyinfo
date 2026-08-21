# video-pipeline

건강정보 숏폼 자동화 파이프라인. `my-video-creator`(단어장/코인뉴스 채널)의 구조를 재사용하되,
건강 니치에 맞게 간결화하고 컴플라이언스 가드레일을 넣었습니다. 근거: [PLAN.md](../PLAN.md) Phase 2.

## 지금 바로 되는 것 (계정 불필요, 테스트 완료)

- **`tts.py`** — Edge TTS로 한국어 여성(`ko-KR-SunHiNeural`)/남성(`ko-KR-InJoonNeural`) 내레이션 생성.
  API 키 없이 동작. `generate_narration_with_captions()`는 문장 단위 타이밍(SentenceBoundary)까지
  같이 반환한다 — 한국어 보이스는 단어 단위(WordBoundary) 타이밍을 지원하지 않아 문장 단위로 자막을
  싱크한다. `python tts.py`로 직접 실행 확인 가능.
- **`compose_video.py`** — 60초 세로(9:16, 1080x1920) 숏폼 영상 합성. 제목 + 문장 단위 자막(자동
  줄바꿈) + 하단 브랜드 워드마크를 다크 배경 위에 렌더링하고 내레이션 오디오를 입혀 mp4로 출력한다.
  ImageMagick 의존성을 피하려고 MoviePy `TextClip` 대신 PIL로 텍스트를 직접 렌더링했다(폰트:
  `assets/fonts/NanumGothic.ttf`, 오픈소스 폰트를 리포에 번들). `python compose_video.py`로 직접
  실행하면 `samples/sample_short.mp4` 생성됨 — 실제 mp4 출력, 프레임 캡처로 렌더링 확인 완료.
  아직 배경 이미지/영상 소재나 효과음은 없음 (단색 배경 + 텍스트만 있는 최소 버전).
- **`script_prompt.py`** — Gemini(`gemini-3.1-flash-lite`, my-video-creator와 동일 키/모델)를 직접
  호출해 대본을 생성한다. `COMPLIANCE_COPY_GUIDE.md`의 금지 표현/필수 고지 규칙이 시스템 프롬프트에
  고정 삽입되어 있고, `response_json_schema`로 출력 형식을 강제한다. 실제 호출 테스트 완료 —
  알레르기·질병 단정 없이, 출처 인용과 필수 고지 문구까지 포함된 대본이 생성됨.
- **`pipeline.py`** — 대본 생성 → 자동 컴플라이언스 점검(금지어 스캔) → **사람 검수(터미널에서 대본을
  보여주고 y/N 확인)** → 음성/자막 생성 → 영상 합성까지 이어지는 엔드투엔드 스크립트.
  `python pipeline.py "주제" "클러스터"`로 실행. 업로드는 자동으로 하지 않고 안내만 출력한다
  (업로드는 별도로 `youtube_upload.upload_video()` 호출). 실제로 3편 생성해서 검증 완료.

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

- 배경 이미지/영상 소재, 효과음, BGM — 지금은 단색 배경 + 텍스트만 있는 최소 버전 (기능 검증 목적).
  비주얼을 더 다듬고 싶으면 `compose_video.py`의 `BG_COLOR`/폰트 크기 등을 조정하거나 배경 레이어를
  추가하면 됨.
- 첫 실제 YouTube 업로드 (파이프라인/인증 모두 준비 끝났고, 업로드 함수만 호출하면 됨)

## 실행 방법

```
python pipeline.py "주제" "콘텐츠 클러스터"
# 예: python pipeline.py "물은 하루에 얼마나 마셔야 할까?" "영양 기초"
```

대본이 나오면 터미널에 표시되고, 자동 컴플라이언스 점검 결과와 함께 진행 여부를 물어본다.
`y`를 입력하면 `output/` 폴더에 mp3(내레이션)와 mp4(완성 영상)가 생성된다.
