import fs from "node:fs";
import path from "node:path";

export interface Article {
  slug: string;
  title: string;
  cluster: string;
  body: string;
  source: string;
  tags: string[];
  youtubeVideoId: string;
  publishedAt: string;
  thumbnailUrl?: string | null;
}

// 5개 콘텐츠 클러스터 — video-pipeline/topic_calendar.py의 CLUSTERS와 동일한 이름을 쓴다.
export const CLUSTERS = ["영양 기초", "증상별 가이드", "식단 비교", "제품 큐레이션", "루틴·기록"];

const ARTICLES_DIR = path.join(process.cwd(), "content", "articles");

function isArticle(value: unknown): value is Article {
  if (!value || typeof value !== "object") return false;
  const a = value as Record<string, unknown>;
  return (
    typeof a.slug === "string" &&
    typeof a.title === "string" &&
    typeof a.cluster === "string" &&
    typeof a.body === "string" &&
    typeof a.youtubeVideoId === "string" &&
    typeof a.publishedAt === "string"
  );
}

export function getAllArticles(): Article[] {
  if (!fs.existsSync(ARTICLES_DIR)) return [];
  const files = fs.readdirSync(ARTICLES_DIR).filter((f) => f.endsWith(".json"));
  const articles = files
    .map((file) => {
      try {
        const raw = JSON.parse(fs.readFileSync(path.join(ARTICLES_DIR, file), "utf-8"));
        return isArticle(raw) ? raw : null;
      } catch {
        return null;
      }
    })
    .filter((a): a is Article => a !== null);

  return articles.sort((a, b) => (a.publishedAt < b.publishedAt ? 1 : -1));
}

export function getArticlesByCluster(cluster: string): Article[] {
  return getAllArticles().filter((a) => a.cluster === cluster);
}

export function getArticleBySlug(slug: string): Article | null {
  return getAllArticles().find((a) => a.slug === slug) ?? null;
}
