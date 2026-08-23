"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase/client";

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M23.52 12.27c0-.82-.07-1.42-.22-2.05H12v3.89h6.6c-.13 1.08-.85 2.72-2.45 3.82l-.02.15 3.56 2.76.25.02c2.26-2.09 3.58-5.17 3.58-8.59Z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.07 7.94-2.9l-3.79-2.93c-1.01.71-2.37 1.21-4.15 1.21-3.17 0-5.86-2.09-6.82-4.98l-.14.01-3.7 2.86-.05.13C3.28 21.3 7.31 24 12 24Z"
      />
      <path
        fill="#FBBC05"
        d="M5.18 14.4A7.4 7.4 0 0 1 4.77 12c0-.83.15-1.64.4-2.4l-.01-.16-3.75-2.9-.12.06A11.96 11.96 0 0 0 0 12c0 1.93.47 3.76 1.29 5.4l3.89-3Z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c2.26 0 3.78.97 4.65 1.79l3.39-3.3C17.94 1.19 15.24 0 12 0 7.31 0 3.28 2.7 1.29 6.6l3.88 3C6.14 6.84 8.83 4.75 12 4.75Z"
      />
    </svg>
  );
}

function KakaoIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
      <path
        fill="#191600"
        d="M12 2C6.48 2 2 5.52 2 9.86c0 2.7 1.74 5.08 4.36 6.47-.19.7-.7 2.57-.8 2.97-.13.5.18.5.38.36.16-.11 2.52-1.72 3.55-2.42.82.12 1.67.19 2.51.19 5.52 0 10-3.52 10-7.86S17.52 2 12 2Z"
      />
    </svg>
  );
}

export function LoginButtons({ next = "/" }: { next?: string }) {
  const [loading, setLoading] = useState<"google" | "kakao" | null>(null);

  async function login(provider: "google" | "kakao") {
    setLoading(provider);
    const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`;
    await supabase.auth.signInWithOAuth({ provider, options: { redirectTo } });
  }

  return (
    <div className="flex flex-col gap-3">
      <button
        type="button"
        onClick={() => login("kakao")}
        disabled={loading !== null}
        className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#FEE500] text-sm font-medium text-[#191600] transition-opacity hover:opacity-90 disabled:opacity-60"
      >
        <KakaoIcon />
        {loading === "kakao" ? "이동 중..." : "카카오로 로그인"}
      </button>
      <button
        type="button"
        onClick={() => login("google")}
        disabled={loading !== null}
        className="flex h-11 w-full items-center justify-center gap-2 rounded-lg border border-border bg-background text-sm font-medium hover:bg-muted disabled:opacity-60"
      >
        <GoogleIcon />
        {loading === "google" ? "이동 중..." : "Google로 로그인"}
      </button>
    </div>
  );
}

export default function LoginPage() {
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="font-heading text-2xl tracking-tight">로그인</h1>
          <p className="text-sm text-muted-foreground">
            로그인하면 내 식단 결과를 계정에 저장하고 어디서든 다시 볼 수 있어요.
          </p>
        </div>
        <LoginButtons />
      </div>
    </main>
  );
}
