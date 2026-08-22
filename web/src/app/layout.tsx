import type { Metadata } from "next";
import Link from "next/link";
import { Geist_Mono, Noto_Sans_KR, Black_Han_Sans } from "next/font/google";
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

// 헤드라인용 — video-pipeline/compose_video.py가 영상 제목/자막에 쓰는 것과 같은
// Black Han Sans를 웹에도 재사용해서 채널과 사이트의 타이포 아이덴티티를 통일.
const blackHanSans = Black_Han_Sans({
  variable: "--font-black-han-sans",
  subsets: ["latin"],
  weight: "400",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "한끼정답 — 맞춤 식단 & 건강정보",
  description: "오늘 뭐 먹지 고민될 때, 내 목표와 활동량에 맞춘 하루 식단 목표를 30초 만에 확인하세요.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${notoSansKr.variable} ${blackHanSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b px-6 py-4">
          <Link href="/" className="font-heading text-lg tracking-tight text-primary">
            한끼정답
          </Link>
        </header>
        {children}
      </body>
    </html>
  );
}
