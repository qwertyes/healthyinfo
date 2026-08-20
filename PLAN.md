# HealthyInfo — 진행 계획

> 이 파일은 진행상황 추적용입니다. 작업을 끝낼 때마다 `[ ]`를 `[x]`로 바꾸고, 맨 위 **진행률**을 갱신하세요.
> 새 세션(다음날 등)에서 작업을 이어갈 때는 이 파일을 먼저 읽고 미완료(`[ ]`) 항목부터 이어서 진행하면 됩니다.

**진행률: 13 / 26 (50%)**

## 사용자 확인이 필요해서 멈춘 항목
- ~~채널명~~ → **확정: 한끼정답 (영문/기술명: Hankki)**
- **도메인 구매**: 보류 — 정식 커스텀 도메인 없이 Vercel 기본 주소(`*.vercel.app`)로 운영
- **Supabase 계정 생성**: 새 이메일로 가입 필요 (사용자 본인만 가능)
- ~~Vercel 계정/프로젝트 생성~~ → **완료, 배포됨: https://hankki-nine.vercel.app**
- **새 YouTube 채널 + Google Cloud OAuth 클라이언트 발급**: 기존 VocaMate(@KoreaNo1.) 채널과 다른 새 채널이 필요, 계정 로그인/동의 화면은 사용자 본인만 가능
→ Supabase, YouTube 두 개만 남았습니다. 준비되면 알려주세요.

## 지금까지 만들어진 것
- **https://hankki-nine.vercel.app** — 실제 배포된 사이트 (Vercel 팀: Hankki, 계정: silvernatural2@gmail.com). GitHub master 브랜치에 push하면 자동 재배포됨.
- `web/` — Next.js 웹앱 (홈 즉시체험 위젯, 온보딩 퀴즈, 결과 리포트, 개인정보/약관 페이지). `npx next dev`로 로컬 확인 가능.
- `video-pipeline/` — TTS 생성(테스트 완료), 대본 생성 프롬프트(컴플라이언스 가드레일 포함), YouTube 업로드 모듈(재사용). 자세한 내용은 `video-pipeline/README.md` 참고.
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

---

## Phase 0 · 뼈대 세팅
- [x] 채널명 확정 → **한끼정답 (Hankki)**
- [x] 도메인 → 보류 결정 (Vercel 기본 주소 사용, 커스텀 도메인 구매 안 함)
- [x] 진단/치료 표현 금지 카피 가이드 문서화 → `COMPLIANCE_COPY_GUIDE.md`
- [x] GitHub `healthyinfo` 리포지토리 생성 (VocaMate와 동일 계정) → https://github.com/qwertyes/healthyinfo
- [ ] Supabase 별도 계정 가입 + 프로젝트 생성
- [x] Vercel 프로젝트 생성 및 GitHub 연동 (Hobby로 시작) → https://hankki-nine.vercel.app (팀: Hankki, 계정: silvernatural2@gmail.com), master 브랜치 push마다 자동 배포됨

## Phase 1 · 웹 MVP
- [x] Next.js(App Router) 프로젝트 스캐폴딩 → `web/` (Next.js 16 + Tailwind + shadcn/ui)
- [ ] Supabase 연동 (DB 스키마: 사용자, 온보딩 응답, 식단 결과) — Supabase 프로젝트 생성 대기
- [x] 홈 즉시체험 위젯 (나이/성별/활동량 입력 → 즉시 식단 미리보기) → `web/src/components/instant-widget.tsx`, BMR/TDEE 계산은 `web/src/lib/nutrition.ts`
- [x] 온보딩 퍼스널라이제이션 퀴즈 (6문항) 구현 → `web/src/components/onboarding/onboarding-quiz.tsx` (답변은 현재 클라이언트 상태에만 저장 — Supabase 연동 후 DB 저장으로 교체 필요)
- [ ] AI 맞춤 식단 생성 로직 (Vercel AI Gateway 연동) — Vercel 프로젝트 생성 대기
- [x] 결과 리포트 화면 + 프리미엄 CTA → 온보딩 완료 시 리포트 화면 표시, 프리미엄 버튼은 결제 연동 전까지 비활성 상태
- [x] 개인정보처리방침/약관 페이지 (건강 민감정보 동의 포함) → `web/src/app/privacy`, `web/src/app/terms` (초안, 법률 자문 전 공개 금지)

## Phase 2 · 영상 파이프라인 이식
- [x] TTS 모듈 작성 → `video-pipeline/tts.py` (Edge TTS, 한국어 여/남 보이스, 실행 검증 완료)
- [x] `youtube_api.py` 복제 → `video-pipeline/youtube_upload.py` (이미 범용적으로 작성돼 있어 그대로 재사용)
- [x] 건강정보 대본 생성 프롬프트 작성 → `video-pipeline/script_prompt.py` (컴플라이언스 가드레일 포함, 실행 검증 완료). 단, 실제 LLM 호출부는 API 키 대기 중 (`generate_script()`가 `NotImplementedError`)
- [ ] 영상 합성 템플릿 제작 (자막/효과음) — 비주얼 스타일 결정 필요, 후순위로 보류
- [ ] 사람 검수 단계 프로세스 정의 (유튜브 비진정성 콘텐츠 정책 대응) — 프로세스는 COMPLIANCE_COPY_GUIDE.md에 체크리스트로 존재, 실제 검수 툴링은 미구현
- [ ] "오늘의 건강 상식" 숏폼 테스트 업로드 1편 — 새 YouTube 채널 + OAuth 클라이언트 발급 필요 (video-pipeline/README.md 참고)

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
