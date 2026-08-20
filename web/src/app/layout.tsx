import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
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
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b px-6 py-4">
          <Link href="/" className="text-sm font-semibold tracking-tight">
            한끼정답
          </Link>
        </header>
        {children}
      </body>
    </html>
  );
}
