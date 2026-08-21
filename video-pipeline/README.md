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
- **`script_prompt.py`** — Gemini(`gemini-3.1-flash-lite`, my-video-creator와 동일 키/모델)로
  대본을 생성한다. **완전 자동화(사람 검수 없음)를 전제로 2단계 구조**: ①검색 전용 호출로
  Google 검색 그라운딩을 통해 사실을 모으고, ②그 사실만 근거로 컴플라이언스 규칙에 맞춰 대본을
  작성한다. 검색 근거가 하나도 없으면 `UnverifiedContentError`를 던져서 자동으로 생성을 막는다 —
  "지어낸 통계"가 나가는 걸 막는 최소 안전장치다. (처음엔 검색+작성을 한 번에 시켰더니 시스템
  프롬프트가 복잡해서 모델이 검색 도구 호출을 자꾸 건너뛰는 문제가 있었고, 2단계로 분리해서
  해결했다.)
- **`pipeline.py`** — 대본 생성(검색 그라운딩 포함) → 자동 컴플라이언스 점검(금지어 스캔, 위반 시
  자동 스킵) → 음성/자막 생성 → 영상 합성까지 **사람 개입 없이** 이어지는 엔드투엔드 스크립트.
  `python pipeline.py "주제" "클러스터"`로 실행. 모든 결과는 `output/*_metadata.json`으로 남아
  나중에 스팟체크할 수 있다. 업로드는 자동으로 하지 않고 안내만 출력한다(별도로
  `youtube_upload.upload_video()` 호출). 완전 자동 모드로 실제 실행해서 검증 완료.

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
