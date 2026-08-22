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
5. **`topic_calendar.py`** — PLAN.md의 5개 콘텐츠 클러스터(영양 기초 / 증상별 가이드 / 식단 비교 /
   제품 큐레이션 / 루틴·기록) 각각에서 주제를 여러 개(기본 5개씩, 총 25개) 한 번에 브레인스토밍해서
   `content_calendar.json`에 라운드로빈으로 섞어 저장한다. 검색 그라운딩이 필요 없는 "무엇을
   다룰지" 단계라 순수 생성만 한다 — 실제 대본(각 항목의 사실 확인)은 여전히 `script_prompt.py`가
   그때그때 검증한다. 큐가 줄어들면 `python topic_calendar.py [클러스터당 개수]`로 다시 채운다.
6. **`pipeline.py`** — 위 전부를 이어붙이는 엔드투엔드 스크립트. 자동 컴플라이언스 점검(금지어
   스캔) 위반 시 영상을 만들지 않고 자동 스킵. 모든 결과는 `output/*_metadata.json`으로 남아
   나중에 스팟체크 가능.
   - **`run(topic=None, cluster=None)`**: 영상만 만들고 업로드는 하지 않는다 (수동 검토용).
     `topic`을 안 주면 `topic_calendar.py`가 쌓아둔 큐에서 하나를 꺼내 쓰고, 그 대본의 예고
     문장은 큐의 **다음** 항목(`upcoming_topic`)을 정확히 가리키도록 강제한다 — Gemini가 즉흥
     으로 다른 주제를 예고해버려서 실제 다음 영상과 어긋나는 걸 방지.
   - **`run_and_upload(...)`**: `run()`과 동일하게 영상을 만들고, 성공하면 설명란
     (`build_description`)과 고정 댓글(`build_pinned_comment`)까지 자동 생성해서 업로드·공개
     전환까지 사람 개입 없이 끝낸다. **`daily_auto_run.py`가 이 함수를 호출하는 무인 실행
     진입점**이다.
   - **예약 게시(`scheduled_publish_at`)**: 기본값은 실행 시각과 무관하게 **그날(KST) 오후
     7시**(`next_publish_time_kst()`)에 유튜브가 자동으로 공개하도록 예약한다. 이걸 쓰면
     `youtube_upload.upload_video()`가 내부적으로 ①unlisted로 올림 → ②고정 댓글 등록 →
     ③private + 예약 시각으로 전환 → 시각이 되면 유튜브가 자동 공개, 순서로 처리한다 —
     `my-video-creator/english_words_short.py`(익일 07:30 예약)와 완전히 같은 패턴이다.
     크론이 새벽에 돌아도 노트북이 저녁까지 켜져 있을 필요가 없다.
   - **`upload_and_comment(...)`**: 예약 없이 즉시 올릴 때 쓰는 저수준 함수. **주의**:
     `privacy_status='private'`로 바로 올린 영상은 `commentThreads.insert`가 몇 분~20분
     넘게 기다려도 403으로 실패하는 걸 실제로 겪었다 (유튜브가 완전 비공개 영상은 댓글 기능
     활성화를 미루는 것으로 추정 — 반면 unlisted로 올리면 거의 즉시 성공). 그래서
     `final_privacy='private'`일 때만 일단 unlisted로 올려서 댓글을 확실히 단 다음 private로
     전환한다.
7. **`daily_auto_run.py`** — WSL cron으로 매일 실행되는 완전 무인 진입점. `pipeline.run_and_upload()`
   하나만 호출한다. 캘린더가 비었거나 컴플라이언스/수치 검증에 걸려 영상이 안 만들어져도
   프로세스가 죽지 않고 로그만 남긴다.

## 스케줄링 (WSL cron)

`my-video-creator`의 English Words(05:00)·CoinNews Daily(05:40) Windows 작업 스케줄러와 API 키를
공유하므로(GEMINI_API_KEY, TYPECAST_API_KEY), 같은 시간대에 돌면 쿼터/리소스가 충돌할 수 있다.
그래서 **06:30**으로 스케줄했다 — 노트북이 켜져 있는 이른 아침에 영상을 만들고, 실제 공개는
`next_publish_time_kst()`로 그날 저녁 7시에 예약한다 (노트북이 저녁에 꺼져 있어도 무관).

```
# WSL(Ubuntu) crontab
30 6 * * * cd /mnt/d/AI/HealthyInfo/video-pipeline && /mnt/c/Users/qwert/AppData/Local/Programs/Python/Python313/python.exe daily_auto_run.py >> logs/daily_run.log 2>&1
```

WSL 자체에 무거운 의존성(moviepy 등)을 새로 설치하지 않고, WSL interop으로 **Windows 쪽
python.exe를 그대로 호출**한다 (이미 필요한 패키지가 다 깔려있고, 경로/자격증명도 그대로 통함).
cron이 도는 시간(제작)과 실제 공개 시간(저녁 7시)을 분리한 게 핵심 — 두 값 다 사용자와 상의해서
정함(2026-08-22).

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

## 실행 방법

```
# 콘텐츠 캘린더 채우기 (최초 1회 또는 큐가 줄어들 때)
python topic_calendar.py

# 영상만 만들기 (업로드 안 함, 수동 검토용)
python pipeline.py                              # 캘린더 큐에서 자동으로 다음 주제
python pipeline.py "주제" "콘텐츠 클러스터"        # 주제 직접 지정 (캘린더 무시)

# 영상 생성부터 업로드·댓글·예약공개까지 전부 (daily_auto_run.py가 이걸 씀)
python -c "import pipeline; pipeline.run_and_upload()"
```

사람 확인 없이 대본 생성부터 mp4 완성까지 자동으로 끝난다. `output/` 폴더에 mp3(내레이션),
mp4(완성 영상), metadata.json(대본/출처/검색 근거 — 나중에 스팟체크용)이 생성된다.
2026-08-22부터 `run_and_upload()`(그리고 `daily_auto_run.py`)는 **기본적으로 전체공개**로
예약 업로드한다 — 사용자가 파이프라인을 검증한 뒤 확정한 방침.
