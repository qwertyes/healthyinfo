import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { DisclaimerNote } from "@/components/disclaimer-note";
import { getAllArticles, getArticleBySlug } from "@/lib/articles";

export async function generateStaticParams() {
  return getAllArticles().map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const article = getArticleBySlug(slug);
  if (!article) return { title: "글을 찾을 수 없어요 — 한끼정답" };
  const title = `${article.title} — 한끼정답`;
  const description = article.body.slice(0, 100);
  return {
    title,
    description,
    openGraph: { title, description, type: "article" },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default async function ArticlePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const article = getArticleBySlug(slug);
  if (!article) notFound();

  const publishedDate = new Date(article.publishedAt).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16 sm:py-24">
      <article className="w-full max-w-2xl space-y-8">
        <div className="space-y-4">
          <Link
            href={`/magazine?cluster=${encodeURIComponent(article.cluster)}`}
            className="text-sm font-medium text-brand hover:underline"
          >
            ← {article.cluster}
          </Link>
          <h1 className="font-heading text-2xl leading-tight tracking-tight text-balance sm:text-3xl">
            {article.title}
          </h1>
          <p className="text-sm text-muted-foreground">{publishedDate}</p>
        </div>

        <div className="overflow-hidden rounded-2xl ring-1 ring-foreground/10">
          <div className="aspect-[9/16] w-full max-w-xs mx-auto">
            <iframe
              src={`https://www.youtube.com/embed/${article.youtubeVideoId}`}
              title={article.title}
              className="h-full w-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>

        <p className="text-base leading-relaxed text-foreground">{article.body}</p>

        {article.source && (
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">출처</span> · {article.source}
          </p>
        )}

        {article.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {article.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                #{tag}
              </Badge>
            ))}
          </div>
        )}

        <DisclaimerNote className="border-t pt-6" />
      </article>
    </main>
  );
}
