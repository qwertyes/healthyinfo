import type { MetadataRoute } from "next";
import { getAllArticles } from "@/lib/articles";

const SITE_URL = "https://hankki-nine.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const staticRoutes: MetadataRoute.Sitemap = [
    { url: SITE_URL, changeFrequency: "daily", priority: 1 },
    { url: `${SITE_URL}/onboarding`, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE_URL}/magazine`, changeFrequency: "daily", priority: 0.9 },
    { url: `${SITE_URL}/privacy`, changeFrequency: "yearly", priority: 0.2 },
    { url: `${SITE_URL}/terms`, changeFrequency: "yearly", priority: 0.2 },
  ];

  const articleRoutes: MetadataRoute.Sitemap = getAllArticles().map((article) => ({
    url: `${SITE_URL}/magazine/${article.slug}`,
    lastModified: article.publishedAt,
    changeFrequency: "monthly",
    priority: 0.6,
  }));

  return [...staticRoutes, ...articleRoutes];
}
