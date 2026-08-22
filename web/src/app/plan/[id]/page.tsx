import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DisclaimerNote } from "@/components/disclaimer-note";
import { MealPlanDisplay } from "@/components/onboarding/meal-plan-display";
import { supabase } from "@/lib/supabase/client";
import type { MealPlan } from "@/lib/meal-plan";
import { DIET_TYPE_LABEL, deriveProfileLabel, type CookingTime, type DietType } from "@/lib/quiz";
import type { Goal } from "@/lib/nutrition";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

interface SubmissionReport {
  id: string;
  goal: Goal;
  diet_type: DietType;
  allergies: string[];
  cooking_time: CookingTime;
  has_condition: boolean;
  target_calories: number;
  protein_g: number;
  fat_g: number;
  carb_g: number;
  meal_plan: MealPlan | null;
}

export const metadata = {
  title: "저장된 식단 결과 — 한끼정답",
};

export default async function SavedPlanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!UUID_RE.test(id)) notFound();

  const { data, error } = await supabase.rpc("get_submission_report", { p_id: id }).single<SubmissionReport>();
  if (error || !data) notFound();

  const profile = deriveProfileLabel({ goal: data.goal, cookingTime: data.cooking_time });

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16 sm:py-24">
      <Card className="w-full max-w-xl">
        <CardHeader>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            나의 리포트
          </span>
          <CardTitle className="text-2xl">{profile}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="rounded-lg border bg-muted/40 p-4 space-y-3">
            <p className="text-2xl font-semibold tabular-nums">
              하루 목표 {data.target_calories.toLocaleString()} kcal
            </p>
            <div className="grid grid-cols-3 gap-2 text-sm tabular-nums">
              <div className="rounded-md bg-background p-2 text-center">
                <div className="text-muted-foreground text-xs">단백질</div>
                <div className="font-medium">{data.protein_g}g</div>
              </div>
              <div className="rounded-md bg-background p-2 text-center">
                <div className="text-muted-foreground text-xs">지방</div>
                <div className="font-medium">{data.fat_g}g</div>
              </div>
              <div className="rounded-md bg-background p-2 text-center">
                <div className="text-muted-foreground text-xs">탄수화물</div>
                <div className="font-medium">{data.carb_g}g</div>
              </div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <p>
              <span className="text-muted-foreground">선호 식단</span>{" "}
              <Badge variant="secondary">{DIET_TYPE_LABEL[data.diet_type]}</Badge>
            </p>
            {data.allergies.length > 0 && (
              <p>
                <span className="text-muted-foreground">제외 식재료</span>{" "}
                {data.allergies.map((a) => (
                  <Badge key={a} variant="outline" className="mr-1">
                    {a}
                  </Badge>
                ))}
              </p>
            )}
          </div>

          {data.meal_plan ? (
            <MealPlanDisplay plan={data.meal_plan} />
          ) : (
            <p className="text-sm text-muted-foreground">
              이 결과는 AI 추천 식단 없이 저장되었어요.
            </p>
          )}

          <DisclaimerNote />
        </CardContent>
      </Card>
    </main>
  );
}
