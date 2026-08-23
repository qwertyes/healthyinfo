export const metadata = {
  title: "이용약관 — 한끼정답",
};

export default function TermsPage() {
  return (
    <main className="flex flex-1 justify-center px-6 py-16">
      <article className="w-full max-w-2xl space-y-8 text-sm leading-relaxed">
        <header className="space-y-2">
          <h1 className="font-heading text-2xl tracking-tight">이용약관</h1>
          <p className="text-muted-foreground">시행일: 작성 예정 (정식 서비스 오픈 전 확정)</p>
        </header>

        <p className="text-muted-foreground">
          본 약관은 초안이며, 정식 서비스 오픈 전 법률 자문을 거쳐 확정합니다.
        </p>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">1. 서비스의 성격</h2>
          <p>
            HealthyInfo는 이용자가 입력한 정보를 바탕으로 <strong>일반적인 영양·건강 정보</strong>를
            제공하는 서비스입니다. 의료 행위(진단, 치료, 처방)를 수행하지 않으며, 제공되는
            정보는 의학적 진단이나 치료를 대체하지 않습니다. 기저질환이 있거나 건강상
            우려가 있는 경우 반드시 전문의와 상담해야 합니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">2. 이용자의 책임</h2>
          <p>
            이용자는 본인의 건강 상태를 정확히 입력할 책임이 있으며, 서비스에서 제공하는
            정보를 실제 식단·생활에 적용하기 전 본인의 판단과 필요시 전문가 상담을 거쳐야
            합니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">3. 면책</h2>
          <p>
            회사는 서비스에서 제공하는 정보의 적용 결과에 대해 법령이 허용하는 범위 내에서
            책임을 제한합니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">4. 유료 서비스</h2>
          <p>
            프리미엄 구독 등 유료 서비스의 결제·환불 조건은 별도 페이지에서 안내합니다.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-medium">5. 약관 변경</h2>
          <p>회사는 관련 법령을 준수하는 범위에서 본 약관을 개정할 수 있으며, 개정 시 사전 공지합니다.</p>
        </section>
      </article>
    </main>
  );
}
