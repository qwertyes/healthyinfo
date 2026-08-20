# HealthyInfo — 진행 계획

> 이 파일은 진행상황 추적용입니다. 작업을 끝낼 때마다 `[ ]`를 `[x]`로 바꾸고, 맨 위 **진행률**을 갱신하세요.
> 새 세션(다음날 등)에서 작업을 이어갈 때는 이 파일을 먼저 읽고 미완료(`[ ]`) 항목부터 이어서 진행하면 됩니다.

**진행률: 7 / 26 (27%)**

## 사용자 확인이 필요해서 멈춘 항목
- **채널명**: "뉴트리로그(NutriLog)"를 제안했지만 아직 확정 승인 안 됨
- **도메인 구매**: 결제가 필요해 임의 진행 안 함
- **Supabase 계정 생성**: 새 이메일로 가입 필요 (사용자 본인만 가능)
- **Vercel 계정/프로젝트 생성**: 로그인 필요 (사용자 본인만 가능)
→ 이 4개가 준비되면 알려주세요. Supabase 프로젝트 URL/키, Vercel 로그인만 있으면 나머지는 이어서 진행 가능합니다.

## 참고 문서 (배경/근거)
- 사업성 검토 (유사 사례, 수익구조, 리스크): https://claude.ai/code/artifact/d45dc067-0a79-4466-8c06-66a1c33549e3
- 실행 설계도 (경쟁분석, 사이트맵, 온보딩 퀴즈, 영상 파이프라인, 인프라 구성): https://claude.ai/code/artifact/852d15fc-dae2-404e-b9fd-9aeea2c187aa

## 확정된 결정사항
- 스택: Next.js(App Router) + Vercel + Supabase
- GitHub: VocaMate와 **같은 계정**, 별도 리포지토리(`healthyinfo`)
- Supabase: VocaMate와 **다른 계정(다른 이메일)** — 무료 프로젝트 2개 한도가 계정 단위라서
- Vercel: 수익화(구독/광고/제휴링크) 시작 전까지 Hobby 무료로 개발, 정식 오픈 시 Pro($20/월)로 전환 필요 (Hobby는 상업적 이용 금지 약관)
- 콘텐츠 표현 원칙: "치료/진단/주치의"급 문구 금지, 일반 정보 제공으로 포지셔닝 (의료법·건강기능식품법 리스크 회피)

---

## Phase 0 · 뼈대 세팅
- [ ] 채널명 확정 (제안: 뉴트리로그/NutriLog — 사용자 확정 대기)
- [ ] 도메인 확정 및 구매
- [x] 진단/치료 표현 금지 카피 가이드 문서화 → `COMPLIANCE_COPY_GUIDE.md`
- [x] GitHub `healthyinfo` 리포지토리 생성 (VocaMate와 동일 계정) → https://github.com/qwertyes/healthyinfo
- [ ] Supabase 별도 계정 가입 + 프로젝트 생성
- [ ] Vercel 프로젝트 생성 및 GitHub 연동 (Hobby로 시작)

## Phase 1 · 웹 MVP
- [x] Next.js(App Router) 프로젝트 스캐폴딩 → `web/` (Next.js 16 + Tailwind + shadcn/ui)
- [ ] Supabase 연동 (DB 스키마: 사용자, 온보딩 응답, 식단 결과) — Supabase 프로젝트 생성 대기
- [x] 홈 즉시체험 위젯 (나이/성별/활동량 입력 → 즉시 식단 미리보기) → `web/src/components/instant-widget.tsx`, BMR/TDEE 계산은 `web/src/lib/nutrition.ts`
- [x] 온보딩 퍼스널라이제이션 퀴즈 (6문항) 구현 → `web/src/components/onboarding/onboarding-quiz.tsx` (답변은 현재 클라이언트 상태에만 저장 — Supabase 연동 후 DB 저장으로 교체 필요)
- [ ] AI 맞춤 식단 생성 로직 (Vercel AI Gateway 연동) — Vercel 프로젝트 생성 대기
- [x] 결과 리포트 화면 + 프리미엄 CTA → 온보딩 완료 시 리포트 화면 표시, 프리미엄 버튼은 결제 연동 전까지 비활성 상태
- [x] 개인정보처리방침/약관 페이지 (건강 민감정보 동의 포함) → `web/src/app/privacy`, `web/src/app/terms` (초안, 법률 자문 전 공개 금지)

## Phase 2 · 영상 파이프라인 이식
- [ ] my-video-creator에서 `make_tts.py`, `youtube_api.py` 복제·정리
- [ ] 건강정보 대본 생성 프롬프트 작성 (팩트체크·컴플라이언스 가드레일 포함)
- [ ] 영상 합성 템플릿 제작 (자막/효과음)
- [ ] 사람 검수 단계 프로세스 정의 (유튜브 비진정성 콘텐츠 정책 대응)
- [ ] "오늘의 건강 상식" 숏폼 테스트 업로드 1편

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
