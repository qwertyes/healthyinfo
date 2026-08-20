import { InstantWidget } from "@/components/instant-widget";

const CONTENT_HIGHLIGHTS = [
  {
    title: "영양 기초",
    desc: "단백질은 하루 몇 그램이 적당할까? 탄수화물과 지방에 대한 흔한 오해까지.",
  },
  {
    title: "증상별 가이드",
    desc: "자꾸 피곤한 이유, 잘 붓는 이유를 식습관 관점에서 짚어봅니다.",
  },
  {
    title: "식단 비교",
    desc: "저탄고지 vs 간헐적 단식, 내 생활 패턴에는 어떤 게 더 맞을까요.",
  },
];

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16 sm:py-24">
      <div className="w-full max-w-5xl space-y-16">
        <section className="grid gap-10 md:grid-cols-2 md:items-start">
          <div className="space-y-4">
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              오늘 뭐 먹지, 이제 고민하지 마세요
            </h1>
            <p className="max-w-md text-muted-foreground">
              나이·활동량·목표만 입력하면 하루 칼로리와 영양소 목표를 바로 계산해드립니다.
              가입 없이 지금 바로 확인해보세요.
            </p>
          </div>
          <InstantWidget />
        </section>

        <section className="space-y-6">
          <h2 className="text-xl font-semibold">건강정보 콘텐츠</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {CONTENT_HIGHLIGHTS.map((item) => (
              <div key={item.title} className="rounded-lg border p-4 space-y-2">
                <h3 className="font-medium">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
