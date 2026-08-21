# HealthyInfo — 진행 계획

> 이 파일은 진행상황 추적용입니다. 작업을 끝낼 때마다 `[ ]`를 `[x]`로 바꾸고, 맨 위 **진행률**을 갱신하세요.
> 새 세션(다음날 등)에서 작업을 이어갈 때는 이 파일을 먼저 읽고 미완료(`[ ]`) 항목부터 이어서 진행하면 됩니다.

**진행률: 19 / 27 (70%)** (Phase 2에서 항목 하나가 둘로 나뉘어 총 개수가 26→27로 조정됨)

## 사용자 확인이 필요해서 멈춘 항목
- ~~채널명~~ → **확정: 한끼정답 (영문/기술명: Hankki)**
- **도메인 구매**: 보류 — 정식 커스텀 도메인 없이 Vercel 기본 주소(`*.vercel.app`)로 운영
- ~~Supabase 계정 생성~~ → **완료** (silvernatural2@gmail.com, 프로젝트 hankki, Seoul 리전)
- ~~Vercel 계정/프로젝트 생성~~ → **완료, 배포됨: https://hankki-nine.vercel.app**
- ~~새 YouTube 채널 + Google Cloud OAuth 클라이언트 발급~~ → **완료** (silvernatural2@gmail.com, 채널명 "한끼정답", GCP 프로젝트 "hankki-video", `video-pipeline/credentials.json` 발급 및 API 호출 테스트 완료)
→ 사용자 확인이 필요한 항목은 모두 끝났습니다. 이제부터는 계정/인프라가 아니라 실제 콘텐츠 제작(영상 템플릿, 대본, 업로드) 작업입니다.

## 완료 — 영상 퀄리티 개선 (2026-08-21)
Phase 2 항목은 전부 체크됐지만, 실제 업로드해본 영상(`video_id: 4DgousvWne0`, 비공개)을 보고
"업로드하기엔 퀄리티가 낮다"는 피드백을 받아 `video-pipeline/compose_video.py`를 v2로 개선:
- [x] 배경 — 정적 단색 대신, numpy로 생성한 그라데이션 + 6초 주기로 은은하게 숨쉬는 원형
  글로우 애니메이션 (외부 이미지/영상 소재 없이 절차적 생성, 프레임마다 재계산 안 해서 빠름)
- [x] 자막 — 페이드인/아웃 + 슬라이드업(ease-out) 애니메이션, 반투명 라운드 패널 배경으로
  가독성도 개선
- [x] 사운드 — 자막 등장마다 짧은 "pop" 효과음 + 아주 낮은 볼륨의 앰비언트 패드(둘 다 numpy로
  직접 합성 — 외부 음원 없어서 라이선스 문제 없음)
- [x] 브랜딩 — 제목 아래 포인트 컬러(오렌지) 언더라인 추가, 워드마크/자막 색상 통일
- 실제 렌더링 후 프레임 캡처로 확인 완료, `pipeline.py`(완전 자동)와 연동 테스트도 통과.
  아직 없는 것: 실제 배경 영상/이미지 소재(스톡 영상), 진짜 녹음된 BGM(라이선스 있는 음원)

## 완료 — 영상 퀄리티 개선 2차 (v3, 2026-08-21)
v2를 실제로 보고도 "너무 단조롭다"는 피드백을 받아, 인기 쇼츠 생성기들이 공통으로 쓰는 기법
3가지를 적용:
- [x] **TTS를 Typecast로 교체** → `video-pipeline/typecast_tts.py`. 목소리는 "필재"
  (지식/정보 콘텐츠에 인기 있는 것으로 확인됨). my-video-creator와 동일한 TYPECAST_API_KEY 재사용.
  **단어 단위 타임스탬프**를 제공해서(edge-tts는 한국어 문장 단위만 지원했음) 카라오케 자막이
  가능해짐
- [x] **카라오케 자막** → 문장 전체가 한번에 뜨던 방식에서, 말하는 단어가 실시간으로 포인트
  컬러로 하이라이트되는 방식으로 변경 (`compose_video.py`의 `group_words_into_lines` +
  `_karaoke_line_clips`)
- [x] **배경 사진을 여러 장으로 전환** → Pexels에서 `image_query`로 사진 3장을 받아 구간별로
  전환 (`stock_photo.search_photos`), 각 구간 켄 번즈 줌인 유지
- [x] **폰트를 Black Han Sans(굵은 임팩트 폰트)로 교체** → 제목/자막용. 나눔고딕은 워드마크에만
  유지. 오픈소스 폰트 리포에 번들(`assets/fonts/BlackHanSans-Regular.ttf`)
- `script_prompt.py`의 출력 스키마에 `image_query`(영어 배경사진 검색어) 필드 추가
- 실제 파이프라인 엔드투엔드 실행으로 검증 완료 (주제: "다이어트 중 야식이 당길 때 대처법")
- **(2026-08-21 추가 피드백 1)** 사용자가 실제 재생해보고 "자막 등장마다 나는 pop 효과음이 시청에
  방해된다"고 지적 → `_build_sfx_track`에서 pop 호출 제거. "나머지는 그런대로 괜찮다"는 피드백 —
  목소리/카라오케 자막/배경 사진 전환/폰트는 그대로 유지
- **(2026-08-21 추가 피드백 2)** "자막 박스가 너무 작고 자주 바뀐다, 2줄은 되어야 가독성이
  좋겠다" → 자막 그룹 기준을 16자→30자로 늘리고, `_render_karaoke_frame`을 여러 줄 레이아웃을
  지원하도록 재작성(`_layout_words`로 줄바꿈을 그룹당 한 번만 계산해 하이라이트가 바뀌어도
  줄바꿈이 안 흔들리게 함)
- **(2026-08-21 추가 피드백 3)** "배경음악 필요할까?"라는 질문에 필요하다고 답함 → 새 API 키
  신청 없이(사용자가 "지금 바로 진행해줘"라고 해서) 코드 진행(Am-F-C-G)이 있는 로파이풍 배경음악을
  절차적으로 합성하도록 `_synthesize_ambient_pad` 개선 (기존엔 화음 하나만 계속 울리는 수준).
- **(2026-08-21 추가 피드백 4)** "무조건 두 줄로 맞추지 말고 마침표·쉼표에서 끊어보면 어떨까" →
  `group_words_into_lines`를 문장부호(`.`,`,`,`!`,`?`) 기준 줄바꿈 우선으로 재작성 (문장부호 없을
  때만 34자 강제 컷 안전장치). "유튜브에서 인기 영상 음원을 다운받아달라"는 요청은 저작권 침해라
  거절 → 대신 **YouTube Studio 오디오 보관함**(공식, 저작자 표시 불필요 라이선스)에서 직접 선택:
  "Corporate Mellow Groove"(Doug Maxwell, 설명형 콘텐츠 취향 제목으로 검색해 발견) 다운로드 →
  `video-pipeline/assets/music/corporate_mellow_groove.mp3`로 리포에 번들(폰트와 동일 패턴,
  `.gitignore`에 `!video-pipeline/assets/music/*.mp3` 예외 추가) → `_load_bgm_track`으로 영상
  길이만큼 루프 + 낮은 볼륨으로 합성, 파일 없으면 기존 절차적 합성 패드로 자동 폴백.
- **(2026-08-22 추가 피드백)** "사람 음성이 작다, 일반 쇼츠 설명 음성 크기로, BGM은 아주 약간만
  작게" → `compose_short`에서 내레이션을 `audio_normalize` 후 볼륨 0.95로 증폭, `BGM_VOLUME`을
  0.10→0.05로 낮춤. 짧은 샘플 대본이 아니라 **실제 파이프라인**(`pipeline.py`, 주제: "커피는
  공복에 마셔도 괜찮을까?")으로 정식 대본·정상 길이(54초) 영상 생성 → 완료.
  - 이 과정에서 버그 2개 발견·수정: (1) 대본에 필수 고지 문구가 빠지면 영상 전체를 버리던 것을,
    "고지 문구 누락"만 있을 때는 자동으로 문구를 붙이고 재검사하도록 `pipeline.py` 개선(다른
    컴플라이언스 위반은 여전히 차단). (2) Windows 콘솔 기본 코드페이지(cp949)가 이모지(⛔✅)를
    못 그려서 `print()`가 크래시하던 문제 → `sys.stdout.reconfigure(encoding="utf-8")`로 해결.
  - 완성 영상(`output/20260822_000549_short.mp4`)을 YouTube에 **비공개**로 업로드 완료
    (video_id: `-K51alq3jqE`). 사용자가 직접 확인 후 전체공개로 전환하기로 함 — 아직 실제
    **첫 공개 업로드**는 사용자 몫으로 남아있음

## 중요 결정 — 사람 검수 제거, 완전 자동화로 전환 (2026-08-21)
사용자가 회사 다니느라 매번 대본을 검수할 시간이 없다고 해서, `pipeline.py`의 사람 검수(y/N
확인) 단계를 없애고 **완전 자동화**로 바꿨습니다. 대신 "잘못된 건강정보가 그대로 나가면 안 된다"는
우려를 아래 방식으로 기계적으로 처리합니다 (Phase 2의 "사람 검수 단계 정의" 항목이 이 내용으로
갱신됨):
- **Google 검색 그라운딩**: `script_prompt.py`가 2단계로 나눠서 생성합니다 — ①순수 검색 전용
  호출로 사실을 모으고 ②그 사실만 근거로 컴플라이언스 규칙에 맞춰 대본을 작성. (처음엔 한 번에
  다 시켰더니 시스템 프롬프트가 복잡해서 모델이 검색을 자꾸 건너뛰는 문제가 있었음 — 그래서
  검색 전용 호출을 분리함.)
- **검색 근거가 0개면 자동 차단**: `UnverifiedContentError`. 즉 "증거 없는 통계는 금지"를 사람이
  아니라 코드가 강제합니다.
- **출처 신뢰도 우선순위**를 프롬프트에 명시 (정부·공공기관 > 학회·의료기관 > 학술지 > 그 외는
  근거로 쓰지 않음).
- **컴플라이언스 키워드 스캔도 자동 게이트**: 위반 있으면 영상 자체를 안 만들고 건너뜀.
- **모든 생성 결과는 `output/*_metadata.json`으로 저장**: 대본, 출처, 검색 근거 URL을 남겨서
  나중에 여유 있을 때 스팟체크할 수 있게 함 (강제는 아님).
- 알아둘 점: 이건 "정확성 100% 보장"이 아니라 "완전히 지어내는 것만 막는" 최소 안전장치입니다.
  검색된 소스 중에도 커머스 사이트 같은 낮은 신뢰도 사이트가 섞여 나올 수 있어, 프롬프트로
  우선순위를 지시했지만 완벽하지는 않습니다.

## 지금까지 만들어진 것
- **https://hankki-nine.vercel.app** — 실제 배포된 사이트 (Vercel 팀: Hankki, 계정: silvernatural2@gmail.com). GitHub master 브랜치에 push하면 자동 재배포됨.
- `web/` — Next.js 웹앱 (홈 즉시체험 위젯, 온보딩 퀴즈, 결과 리포트, 개인정보/약관 페이지). `npx next dev`로 로컬 확인 가능.
- `video-pipeline/` — TTS 생성(테스트 완료), 대본 생성 프롬프트(컴플라이언스 가드레일 포함), YouTube 업로드 모듈(재사용), **credentials.json 발급 완료 및 채널 API 호출 검증 완료** (채널: 한끼정답, 계정: silvernatural2@gmail.com). 자세한 내용은 `video-pipeline/README.md` 참고.
- `COMPLIANCE_COPY_GUIDE.md` — 모든 카피/대본 작성 시 지켜야 할 표현 규칙.

## 참고 문서 (배경/근거)
- 사업성 검토 (유사 사례, 수익구조, 리스크): https://claude.ai/code/artifact/d45dc067-0a79-4466-8c06-66a1c33549e3
- 실행 설계도 (경쟁분석, 사이트맵, 온보딩 퀴즈, 영상 파이프라인, 인프라 구성): https://claude.ai/code/artifact/852d15fc-dae2-404e-b9fd-9aeea2c187aa

## 확정된 결정사항
- 브랜드명: **한끼정답** (영문/기술명: Hankki) — repo/디렉토리명은 `healthyinfo` 그대로 유지
- 도메인: 커스텀 도메인 구매 보류, Vercel 기본 주소(`*.vercel.app`) 사용
- 스택: Next.js(App Router) + Vercel + Supabase
- GitHub: VocaMate와 **같은 계정**, 별도 리포지토리(`healthyinfo`)
- Supabase: VocaMate와 **다른 계정(다른 이메일)** — 무료 프로젝트 2개 한도가 계정 단위라서
- Vercel: 수익화(구독/광고/제휴링크) 시작 전까지 Hobby 무료로 개발, 정식 오픈 시 Pro($20/월)로 전환 필요 (Hobby는 상업적 이용 금지 약관). 계정: silvernatural2@gmail.com, 팀명 "Hankki", 프로젝트명 "hankki" → https://hankki-nine.vercel.app
- 콘텐츠 표현 원칙: "치료/진단/주치의"급 문구 금지, 일반 정보 제공으로 포지셔닝 (의료법·건강기능식품법 리스크 회피)
- AI 식단 생성: Vercel AI Gateway가 아니라 **Google Gemini 직접 호출**(`@ai-sdk/google`) 사용. GEMINI_API_KEY는 my-video-creator(VocaMate)와 **동일한 프로덕션 키를 재사용** (GCS `my-video-shorts-bucket/configs/config.json`에서 확인, 사용자가 명시적으로 재사용 결정 — 트래픽 늘면 VocaMate와 쿼터 경쟁 가능성 있음, 필요시 분리 키로 전환)
- YouTube: 계정 silvernatural2@gmail.com, 채널명 "한끼정답", Google Cloud 프로젝트 "hankki-video" (VocaMate와 별도). OAuth는 아직 "테스트" 상태(silvernatural2@gmail.com이 테스트 사용자로 등록됨) — 정식 공개 전환은 Phase 4 수익화 단계에서 필요시 진행
- 영상 TTS: **Typecast** 사용(목소리 "필재"), GEMINI_API_KEY와 마찬가지로 my-video-creator(VocaMate)와 **동일한 TYPECAST_API_KEY 재사용**
- 영상 배경 사진: **Pexels API** 사용, silvernatural2@gmail.com 계정으로 새로 발급(PEXELS_API_KEY)
- `video-pipeline/`의 API 키들은 `video-pipeline/.env` 파일로 관리 (python-dotenv, gitignore 처리됨) — 이전엔 터미널에 직접 입력했지만 키가 3개(Gemini/Pexels/Typecast)로 늘어나서 파일로 전환

---

## Phase 0 · 뼈대 세팅
- [x] 채널명 확정 → **한끼정답 (Hankki)**
- [x] 도메인 → 보류 결정 (Vercel 기본 주소 사용, 커스텀 도메인 구매 안 함)
- [x] 진단/치료 표현 금지 카피 가이드 문서화 → `COMPLIANCE_COPY_GUIDE.md`
- [x] GitHub `healthyinfo` 리포지토리 생성 (VocaMate와 동일 계정) → https://github.com/qwertyes/healthyinfo
- [x] Supabase 별도 계정 가입 + 프로젝트 생성 → 프로젝트 "hankki", 리전 ap-northeast-2(Seoul), URL/Publishable key는 `web/.env.local`에 저장(gitignore 처리됨, GitHub엔 없음)
- [x] Vercel 프로젝트 생성 및 GitHub 연동 (Hobby로 시작) → https://hankki-nine.vercel.app (팀: Hankki, 계정: silvernatural2@gmail.com), master 브랜치 push마다 자동 배포됨

## Phase 1 · 웹 MVP
- [x] Next.js(App Router) 프로젝트 스캐폴딩 → `web/` (Next.js 16 + Tailwind + shadcn/ui)
- [x] Supabase 연동 (DB 스키마: 사용자, 온보딩 응답, 식단 결과) → `supabase/migrations/0001_init.sql` (profiles, onboarding_submissions, RLS 정책) 적용 완료. `web/src/lib/supabase/client.ts` 클라이언트 작성, 실제 배포 사이트에서 온보딩 퀴즈 → 저장까지 브라우저로 테스트 완료
- [x] 홈 즉시체험 위젯 (나이/성별/활동량 입력 → 즉시 식단 미리보기) → `web/src/components/instant-widget.tsx`, BMR/TDEE 계산은 `web/src/lib/nutrition.ts`
- [x] 온보딩 퍼스널라이제이션 퀴즈 (6문항) 구현 → `web/src/components/onboarding/onboarding-quiz.tsx`, 결과 화면에서 이메일(선택) + Supabase 저장까지 연결됨
- [x] AI 맞춤 식단 생성 로직 → `web/src/app/api/meal-plan/route.ts` + `web/src/lib/meal-plan.ts`. Vercel AI Gateway 대신 **Gemini(gemini-3.1-flash-lite) 직접 호출**로 변경 (my-video-creator와 동일한 GEMINI_API_KEY 재사용, 사용자 확인 완료). 로컬 + 배포 사이트 모두 브라우저로 끝까지 테스트 완료 (알레르기 제외, 칼로리 근사, 식단유형 반영 확인)
- [x] 결과 리포트 화면 + 프리미엄 CTA → 온보딩 완료 시 리포트 화면 표시, 프리미엄 버튼은 결제 연동 전까지 비활성 상태
- [x] 개인정보처리방침/약관 페이지 (건강 민감정보 동의 포함) → `web/src/app/privacy`, `web/src/app/terms` (초안, 법률 자문 전 공개 금지)

## Phase 2 · 영상 파이프라인 이식
- [x] TTS 모듈 작성 → `video-pipeline/tts.py` (Edge TTS, 한국어 여/남 보이스, 실행 검증 완료)
- [x] `youtube_api.py` 복제 → `video-pipeline/youtube_upload.py` (이미 범용적으로 작성돼 있어 그대로 재사용)
- [x] 건강정보 대본 생성 프롬프트 작성 → `video-pipeline/script_prompt.py`. Gemini(gemini-3.1-flash-lite) 직접 호출로 실제 구현 완료(`response_json_schema`로 출력 형식 강제), 컴플라이언스 가드레일 포함, 실제 대본 3편 생성 검증
- [x] 영상 합성 템플릿 제작 → `video-pipeline/compose_video.py` (9:16 1080x1920, 문장 단위 자막 자동 줄바꿈, 브랜드 워드마크). 실제 mp4 생성 후 프레임 캡처로 렌더링 확인 완료. 배경은 단색(기능 검증용 최소 버전), 배경 이미지·효과음·BGM은 아직 없음
- [x] 사람 검수 단계 프로세스 정의 → (2026-08-21 갱신) 사용자가 검수할 시간이 없다고 해서 **사람 확인(y/N)을 제거하고 완전 자동화**로 전환. 대신 검색 그라운딩 기반 자동 사실검증(`UnverifiedContentError`) + 컴플라이언스 키워드 자동 차단 + 모든 결과를 `metadata.json`으로 기록해 나중에 스팟체크 가능하게 함. 상세 내용은 위 "중요 결정" 섹션 참고
- [x] "오늘의 건강 상식" 숏폼 테스트 업로드 1편 → video_id `4DgousvWne0`, **비공개(private)**로 업로드 완료 (`video-pipeline/test_upload.py`). 사용자가 실제 영상 재생해본 결과 "업로드하기엔 퀄리티가 낮다"는 피드백 — 배경/자막 애니메이션/사운드/브랜딩 4가지 전부 개선 필요하다고 확인됨. 다음 작업은 비주얼/오디오 퀄리티 개선

## Phase 3 · 연결 고리 구축
- [ ] 영상 설명란/고정댓글 웹사이트 링크 템플릿화
- [ ] 매거진 콘텐츠 클러스터 초안 작성 (5개 클러스터)
- [ ] 콘텐츠 캘린더 운영 시작 (주간 케이던스)

## Phase 4 · 수익화 등록
- [ ] 유튜브 파트너 프로그램 조건 충족 확인 및 신청
- [ ] 쿠팡파트너스 제휴 계정 개설
- [ ] 아이허브 제휴 계정 개설
- [ ] 웹사이트 프리미엄 결제 연동 활성화
- [ ] Vercel Pro로 업그레이드 (수익 발생 시점)
