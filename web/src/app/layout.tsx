import type { Metadata } from "next";
import Link from "next/link";
import { Geist_Mono, Gowun_Batang, Noto_Sans_KR, Black_Han_Sans } from "next/font/google";
import "./globals.css";

// 본문/UI용 — 한글 글리프를 지원하는 폰트로 교체 (기존 Geist는 latin 서브셋뿐이라
// 한글 텍스트는 사실상 브라우저 기본 폰트로 렌더링되고 있었음).
// next/font/google의 CJK 폰트는 subsets로 한글을 따로 선택할 수 없다 — 한글 글리프가
// 기본으로 포함되고, subsets 옵션은 추가로 곁들일 라틴 계열 스크립트만 고른다.
const notoSansKr = Noto_Sans_KR({
  variable: "--font-noto-sans-kr",
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
});

// 헤드라인용 — "세련되고 지적인" 톤으로 재정비하면서 도입한 한글 세리프. 절제된 획 디테일이
// 에디토리얼(매거진) 톤에 맞아서, 굵고 임팩트 있던 Black Han Sans 대신 "읽는" 자리의 기본
// 헤드라인 서체로 쓴다.
const gowunBatang = Gowun_Batang({
  variable: "--font-gowun-batang",
  subsets: ["latin"],
  weight: ["400", "700"],
});

// video-pipeline/compose_video.py가 영상 제목/자막에 쓰는 것과 같은 폰트 — 채널과의
// 연결점을 남기기 위해 헤더 워드마크 등 작은 브랜드 터치로만 쓴다(헤드라인 전체엔 안 씀).
const blackHanSans = Black_Han_Sans({
  variable: "--font-black-han-sans",
  subsets: ["latin"],
  weight: "400",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_TITLE = "한끼정답 — 맞춤 식단 & 건강정보";
const SITE_DESCRIPTION = "오늘 뭐 먹지 고민될 때, 내 목표와 활동량에 맞춘 하루 식단 목표를 30초 만에 확인하세요.";

export const metadata: Metadata = {
  metadataBase: new URL("https://hankki-nine.vercel.app"),
  title: SITE_TITLE,
  description: SITE_DESCRIPTION,
  openGraph: {
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    siteName: "한끼정답",
    locale: "ko_KR",
    type: "website",
    images: ["/hero-meal.jpg"],
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    images: ["/hero-meal.jpg"],
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${notoSansKr.variable} ${gowunBatang.variable} ${blackHanSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b px-6 py-4">
          <Link href="/" className="font-brand text-base tracking-tight text-brand">
            한끼정답
          </Link>
        </header>
        {children}
      </body>
    </html>
  );
}
