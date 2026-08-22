import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { CLUSTERS, getAllArticles } from "@/lib/articles";

export const metadata = {
  title: "건강정보 매거진 — 한끼정답",
  description: "영양 기초부터 식단 비교까지, 검증된 출처를 담은 건강 정보 아티클 모음.",
};

export default async function MagazinePage({
  searchParams,
}: {
  searchParams: Promise<{ cluster?: string }>;
}) {
  const { cluster } = await searchParams;
  const activeCluster = cluster && CLUSTERS.includes(cluster) ? cluster : null;

  const allArticles = getAllArticles();
  const articles = activeCluster
    ? allArticles.filter((a) => a.cluster === activeCluster)
    : allArticles;

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16 sm:py-24">
      <div className="w-full max-w-5xl space-y-8">
        <div className="space-y-2">
          <h1 className="font-heading text-3xl tracking-tight">건강정보 매거진</h1>
          <p className="text-muted-foreground">
            검색으로 확인한 출처만 근거로 삼아 쓴 건강 정보를 모아둡니다.
          </p>
        </div>

        <nav className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b pb-4 text-sm">
          <Link
            href="/magazine"
            className={`font-medium tracking-tight ${
              !activeCluster ? "text-brand" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            전체
          </Link>
          {CLUSTERS.map((c) => (
            <Link
              key={c}
              href={`/magazine?cluster=${encodeURIComponent(c)}`}
              className={`font-medium tracking-tight ${
                activeCluster === c ? "text-brand" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {c}
            </Link>
          ))}
        </nav>

        {articles.length === 0 ? (
          <p className="py-12 text-center text-muted-foreground">
            {activeCluster ? `"${activeCluster}" 카테고리는 아직 준비 중이에요.` : "아직 발행된 글이 없어요."}
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {articles.map((article) => (
              <Link
                key={article.slug}
                href={`/magazine/${article.slug}`}
                className="group flex flex-col gap-2 rounded-xl border p-5 transition-colors hover:border-brand/50 hover:bg-accent"
              >
                <Badge variant="outline" className="w-fit text-muted-foreground">
                  {article.cluster}
                </Badge>
                <h2 className="font-heading text-base leading-snug tracking-tight">
                  {article.title}
                </h2>
                <p className="line-clamp-2 text-sm text-muted-foreground">{article.body}</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
