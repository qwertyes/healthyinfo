export const metadata = {
  title: "개인정보처리방침 — 한끼정답",
};

export default function PrivacyPage() {
  return (
    <main className="flex flex-1 justify-center px-6 py-16">
      <article className="w-full max-w-2xl space-y-8 text-sm leading-relaxed">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">개인정보처리방침</h1>
          <p className="text-muted-foreground">시행일: 작성 예정 (정식 서비스 오픈 전 확정)</p>
        </header>

        <p className="text-muted-foreground">
          HealthyInfo(이하 &ldquo;회사&rdquo;)는 이용자의 개인정보를 중요하게 생각하며,
          「개인정보 보호법」 등 관련 법령을 준수합니다. 본 방침은 초안이며, 정식 서비스
          오픈 전 법률 자문을 거쳐 확정합니다.
        </p>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">1. 수집하는 개인정보 항목</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>필수: 이메일, 비밀번호(또는 소셜 로그인 식별자)</li>
            <li>맞춤 식단 계산을 위한 정보: 성별, 나이, 키, 체중, 활동량, 목표</li>
            <li>
              <strong>민감정보(선택 입력)</strong>: 알레르기, 선호 식단, 기저질환 여부 및 메모.
              이 항목은 이용자가 직접 입력을 선택한 경우에만 수집되며, 별도 동의를 받습니다.
            </li>
            <li>서비스 이용 기록: 접속 로그, 쿠키, 기기 정보</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">2. 수집 목적</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>회원 가입 및 본인 확인</li>
            <li>AI 기반 맞춤 식단·영양 정보 제공 (일반 정보 제공 목적이며, 의학적 진단·치료가 아닙니다)</li>
            <li>서비스 개선 및 부정 이용 방지</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">3. 민감정보(건강정보) 처리에 관한 별도 동의</h2>
          <p>
            기저질환·알레르기 등 건강 관련 정보는 「개인정보 보호법」상 민감정보에 해당합니다.
            회사는 이용자가 온보딩 과정에서 별도로 동의한 경우에만 이를 수집하며, 맞춤 식단
            제안 이외의 목적으로 사용하지 않습니다. 동의를 거부해도 기본 서비스 이용에는
            제한이 없습니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">4. 보유 및 이용 기간</h2>
          <p>
            회원 탈퇴 시 지체 없이 파기하며, 관계 법령에 따라 보존이 필요한 정보는 해당
            기간 동안 별도 보관합니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">5. 제3자 제공 및 처리 위탁</h2>
          <p>
            법령에 근거하거나 이용자 동의가 있는 경우를 제외하고 개인정보를 외부에 제공하지
            않습니다. 서비스 운영을 위해 데이터베이스·인증(Supabase), 호스팅(Vercel) 등
            인프라 제공업체에 처리를 위탁할 수 있습니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">6. 이용자의 권리</h2>
          <p>
            이용자는 언제든 자신의 개인정보 열람, 정정, 삭제, 처리 정지를 요청할 수 있습니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">7. 문의처</h2>
          <p>개인정보 관련 문의는 서비스 내 문의 채널을 통해 접수해주세요.</p>
        </section>
      </article>
    </main>
  );
}
