import Image from "next/image";
import Link from "next/link";
import { InstantWidget } from "@/components/instant-widget";

const YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@hankki_jeongdap";

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
          <div className="space-y-6">
            <div className="space-y-4">
              <h1 className="font-heading text-3xl leading-tight tracking-tight text-balance sm:text-4xl">
                오늘 뭐 먹지, 이제 고민하지 마세요
              </h1>
              <p className="max-w-md text-muted-foreground">
                나이·활동량·목표만 입력하면 하루 칼로리와 영양소 목표를 바로 계산해드립니다.
                가입 없이 지금 바로 확인해보세요.
              </p>
            </div>
            <div className="overflow-hidden rounded-2xl ring-1 ring-foreground/10">
              <Image
                src="/hero-meal.jpg"
                alt="다양한 채소와 단백질이 담긴 건강한 한 끼 샐러드 볼"
                width={800}
                height={1200}
                className="h-64 w-full object-cover sm:h-80"
                priority
              />
            </div>
          </div>
          <InstantWidget />
        </section>

        <section className="space-y-6">
          <div className="flex items-baseline justify-between gap-4">
            <h2 className="font-heading text-xl tracking-tight">건강정보 콘텐츠</h2>
            <Link
              href={YOUTUBE_CHANNEL_URL}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-medium text-brand hover:underline"
            >
              채널에서 더 보기 →
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {CONTENT_HIGHLIGHTS.map((item) => (
              <Link
                key={item.title}
                href={YOUTUBE_CHANNEL_URL}
                target="_blank"
                rel="noreferrer"
                className="group space-y-2 rounded-xl border p-5 transition-colors hover:border-brand/50 hover:bg-accent"
              >
                <h3 className="font-heading text-base tracking-tight">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
                <span className="inline-block text-sm font-medium text-brand opacity-0 transition-opacity group-hover:opacity-100">
                  유튜브에서 보기 →
                </span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
