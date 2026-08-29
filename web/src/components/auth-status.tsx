"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase/client";

export function AuthStatus() {
  const [user, setUser] = useState<User | null>(null);
  const [loaded, setLoaded] = useState(false);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      setLoaded(true);
    });
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.subscription.unsubscribe();
  }, []);

  if (!loaded) return null;

  if (!user) {
    return (
      <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground">
        로그인
      </Link>
    );
  }

  const label = user.user_metadata?.name ?? user.user_metadata?.full_name ?? user.email ?? "내 계정";

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <Link href="/plan" className="font-medium text-muted-foreground hover:text-foreground">
        내 기록
      </Link>
      <button
        type="button"
        className="font-medium text-muted-foreground hover:text-foreground"
        onClick={async () => {
          await supabase.auth.signOut();
          router.refresh();
        }}
      >
        로그아웃
      </button>
    </div>
  );
}
