import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/server";
import { GOAL_LABEL } from "@/lib/nutrition";
import { DIET_TYPE_LABEL, type DietType } from "@/lib/quiz";
import type { Goal } from "@/lib/nutrition";

interface SavedPlanRow {
  id: string;
  goal: Goal;
  diet_type: DietType;
  target_calories: number;
  created_at: string;
}

export const metadata = {
  title: "내 식단 기록 — 한끼정답",
};

export default async function MyPlansPage() {
  const supabase = await createClient();
  const { data: userData } = await supabase.auth.getUser();

  if (!userData.user) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        <div className="max-w-sm space-y-4">
          <h1 className="font-heading text-2xl tracking-tight">내 식단 기록</h1>
          <p className="text-sm text-muted-foreground">
            로그인하면 그동안 저장한 식단 기록을 여기서 한눈에 볼 수 있어요.
          </p>
          <Link href="/login" className={buttonVariants({ className: "w-full" })}>
            로그인하기
          </Link>
        </div>
      </main>
    );
  }

  const { data: rows, error } = await supabase
    .from("onboarding_submissions")
    .select("id, goal, diet_type, target_calories, created_at")
    .eq("user_id", userData.user.id)
    .order("created_at", { ascending: false })
    .returns<SavedPlanRow[]>();

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16">
      <div className="w-full max-w-xl space-y-6">
        <h1 className="font-heading text-2xl tracking-tight">내 식단 기록</h1>

        {error && <p className="text-sm text-destructive">기록을 불러오지 못했습니다: {error.message}</p>}

        {!error && (!rows || rows.length === 0) && (
          <Card>
            <CardContent className="space-y-3 py-8 text-center">
              <p className="text-sm text-muted-foreground">아직 저장한 식단 기록이 없어요.</p>
              <Link href="/onboarding" className={buttonVariants()}>
                맞춤 식단 받아보기
              </Link>
            </CardContent>
          </Card>
        )}

        <div className="space-y-3">
          {(rows ?? []).map((row) => (
            <Link key={row.id} href={`/plan/${row.id}`}>
              <Card className="transition-colors hover:bg-muted/40">
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle className="text-base">
                    하루 목표 {row.target_calories.toLocaleString()} kcal
                  </CardTitle>
                  <span className="text-xs text-muted-foreground">
                    {new Date(row.created_at).toLocaleDateString("ko-KR", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </CardHeader>
                <CardContent className="flex gap-2">
                  <Badge variant="secondary">{GOAL_LABEL[row.goal]}</Badge>
                  <Badge variant="outline">{DIET_TYPE_LABEL[row.diet_type]}</Badge>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
