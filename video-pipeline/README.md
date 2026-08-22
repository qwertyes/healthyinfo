# video-pipeline

건강정보 숏폼 자동화 파이프라인. `my-video-creator`(단어장/코인뉴스 채널)의 구조를 재사용하되,
건강 니치에 맞게 간결화하고 컴플라이언스 가드레일을 넣었습니다. 근거: [PLAN.md](../PLAN.md) Phase 2.

**완전 자동 모드**로 설계되어 있습니다 — 사람 검수 없이 매일 실행하는 걸 전제로,
검색 그라운딩 기반 자동 사실확인 + 컴플라이언스 키워드 스캔이 안전장치 역할을 합니다.

## 파이프라인 구성

1. **`script_prompt.py`** — Gemini(`gemini-3.1-flash-lite`, my-video-creator와 동일 키/모델)로
   대본을 생성한다. 2단계 구조: ①검색 전용 호출로 Google 검색 그라운딩을 통해 사실을 모으고,
   ②그 사실만 근거로 컴플라이언스 규칙에 맞춰 대본 + 배경사진 검색어(`image_query`)를 작성한다.
   검색 근거가 하나도 없으면 `UnverifiedContentError`로 자동 차단 — "지어낸 통계"가 나가는 걸
   막는 최소 안전장치다. (검색+작성을 한 번에 시켰더니 모델이 검색 도구 호출을 자꾸 건너뛰는
   문제가 있어서, 리서치 전용 호출과 작성 전용 호출로 분리해서 해결했다.)
2. **`typecast_tts.py`** — Typecast API로 내레이션 생성. 목소리는 **"필재"** —
   [지식/정보성 콘텐츠에 인기 있는 것으로 확인된 보이스](https://typecast.ai/kr/learn/typecast-piljae-ai-voice-youtube-shorts/).
   **단어 단위 타임스탬프**까지 받아와서 카라오케 자막에 쓴다. (구버전 `tts.py`는 edge-tts 기반—
   API 키 없이 동작하는 무료 폴백으로 남겨둠. 문장 단위 타이밍만 지원.)
3. **`stock_photo.py`** — Pexels API로 대본의 `image_query`에 맞는 배경 사진을 여러 장(기본 3장)
   검색·다운로드. 무료 API, 상업적 유튜브 영상에도 라이선스 문제 없음(Pexels License).
4. **`compose_video.py`** — 9:16(1080x1920) 숏폼 영상 합성:
   - 배경: 스톡 사진 여러 장을 구간별로 전환하며 각 구간 켄 번즈 줌인. 사진을 못 구하면
     numpy로 생성한 그라데이션+숨쉬는 글로우 배경으로 자동 폴백.
   - 자막: **단어 단위 카라오케 하이라이트** (말하는 단어가 포인트 컬러로 강조됨), 반투명 패널.
   - 폰트: 제목/자막은 **Black Han Sans**(굵고 임팩트 있는 무료 한글 폰트), 브랜드 워드마크는
     나눔고딕. 둘 다 오픈소스 폰트를 리포에 직접 번들(`assets/fonts/`) — 외부 이미지·영상·음원
     소재 없이 전부 절차적으로 생성해서 라이선스 걱정이 없다.
   - 사운드: **YouTube Studio 오디오 보관함**(공식, 저작자 표시 불필요 라이선스)에서 받은 실제
     BGM — "Corporate Mellow Groove"(Doug Maxwell, 설명형 콘텐츠에 흔히 쓰이는 잔잔한 트랙) —
     을 `assets/music/corporate_mellow_groove.mp3`로 리포에 번들해서 영상 길이만큼 루프 +
     낮은 볼륨(`BGM_VOLUME=0.10`)으로 깐다 (`_load_bgm_track`). 파일이 없을 때만 예전처럼
     코드 진행(Am-F-C-G) 절차적 합성 패드로 자동 폴백한다 (`_synthesize_ambient_pad`).
     (자막 줄마다 "pop" 효과음도 넣어봤는데, 실제로 들어보니 시청에 방해된다는 피드백을 받아
     뺐다 — `_synthesize_pop`은 코드로는 남아있지만 호출하지 않음.)
   - 자막은 **문장부호(마침표·쉼표·느낌표·물음표) 기준으로 끊어서** 그룹으로 묶는다 —
     무조건 두 줄로 맞추니 끊어 읽기가 부자연스럽다는 피드백을 반영 (`group_words_into_lines`).
     문장부호가 없을 때만 34자에서 강제로 끊는 안전장치가 있다. `_layout_words`가 줄바꿈을
     그룹당 한 번만 계산해서, 하이라이트 단어가 바뀌어도 줄바꿈/박스 크기가 흔들리지 않는다.
   - ImageMagick 의존성을 피하려고 MoviePy `TextClip` 대신 PIL로 텍스트를 직접 렌더링했고,
     MoviePy 1.0.3의 내장 `.resize()`가 최신 Pillow(10+)에서 깨지는 버그(`Image.ANTIALIAS` 제거됨)를
     피하려고 켄 번즈 줌도 직접 프레임 생성으로 구현했다.
5. **`pipeline.py`** — 위 전부를 이어붙이는 엔드투엔드 스크립트. 자동 컴플라이언스 점검(금지어
   스캔) 위반 시 영상을 만들지 않고 자동 스킵. 모든 결과는 `output/*_metadata.json`으로 남아
   나중에 스팟체크 가능. 업로드는 자동으로 하지 않고 안내만 출력.
   - **예고 문구 자동 이어받기**: 대본이 구조화된 `next_topic_hint` 필드로 남긴 "다음 편" 주제를
     `content_queue.json`에 저장한다. `python pipeline.py`를 **인자 없이** 실행하면 직전 영상이
     예고한 주제를 자동으로 이어서 진행 — 예고가 그냥 빈말이 되지 않게 하는 장치.
   - **`build_pinned_comment(source, next_topic_hint)` / `upload_and_comment(...)`**: 업로드 시
     달 고정 댓글(출처 재확인 + 다음 편 예고 + 소통 유도 + 필수 고지 문구)을 메타데이터로부터
     자동 생성하고 등록한다. **주의**: `privacy_status='private'`로 바로 올린 영상은
     `commentThreads.insert`가 몇 분~20분 넘게 기다려도 403으로 실패하는 걸 실제로 겪었다
     (유튜브가 완전 비공개 영상은 댓글 기능 활성화를 미루는 것으로 추정 — 반면 '일부공개
     (unlisted)'로 올리면 거의 즉시 성공). 그래서 `upload_and_comment()`는 최종적으로 private로
     남기고 싶어도 **일단 unlisted로 올려서 댓글을 확실히 단 다음 private로 전환**하는 절차를
     쓴다 (`my-video-creator/english_words_short.py`가 예약 발행 때 굳이 unlisted를 거치는 것도
     같은 이유로 보임). 앞으로 업로드할 땐 `upload_video()`를 직접 쓰지 말고 이 함수를 쓸 것.

## 완료된 것 (채널/인증)

- **YouTube 채널**: "한끼정답" (계정 silvernatural2@gmail.com, VocaMate `@KoreaNo1.`과 별도)
- **Google Cloud 프로젝트**: `hankki-video`, YouTube Data API v3 활성화됨
- **OAuth 클라이언트**: 데스크톱 앱 타입, `client_secret.json`으로 로컬에 저장(gitignore 처리)
- **`credentials.json`**: `generate_credentials.py`로 1회 인증 완료, `youtube.upload` +
  `youtube.force-ssl` 스코프 보유. 첫 테스트 업로드(비공개, video_id `4DgousvWne0`) 완료.
- OAuth 앱은 아직 **"테스트" 상태** — silvernatural2@gmail.com이 테스트 사용자로 등록되어 있어
  본인 계정으로는 계속 사용 가능.

## 환경변수 (`.env`, gitignore 처리됨)

```
GEMINI_API_KEY=...       # my-video-creator(VocaMate)와 동일 키 재사용
PEXELS_API_KEY=...       # silvernatural2@gmail.com 계정으로 발급
TYPECAST_API_KEY=...     # my-video-creator(VocaMate)와 동일 키 재사용
```

## 아직 만들지 않은 것

- 첫 실제 **공개** 업로드 (지금까지는 비공개 테스트 업로드만 진행)

## 실행 방법

```
python pipeline.py "주제" "콘텐츠 클러스터"
# 예: python pipeline.py "물은 하루에 얼마나 마셔야 할까?" "영양 기초"
```

사람 확인 없이 대본 생성부터 mp4 완성까지 자동으로 끝난다. `output/` 폴더에 mp3(내레이션),
mp4(완성 영상), metadata.json(대본/출처/검색 근거 — 나중에 스팟체크용)이 생성된다.
