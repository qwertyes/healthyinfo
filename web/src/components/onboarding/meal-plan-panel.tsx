"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DIET_TYPE_LABEL, type QuizAnswers } from "@/lib/quiz";
import { GOAL_LABEL, type NutritionResult } from "@/lib/nutrition";
import type { MealPlan } from "@/lib/meal-plan";

const SLOT_LABEL: Record<MealPlan["meals"][number]["slot"], string> = {
  breakfast: "아침",
  lunch: "점심",
  dinner: "저녁",
  snack: "간식",
};

export function MealPlanPanel({
  answers,
  result,
}: {
  answers: QuizAnswers;
  result: NutritionResult;
}) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [plan, setPlan] = useState<MealPlan | null>(null);

  async function generate() {
    setState("loading");
    try {
      const res = await fetch("/api/meal-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal: GOAL_LABEL[answers.goal],
          dietType: DIET_TYPE_LABEL[answers.dietType],
          allergies: answers.allergies,
          cookingTime: answers.cookingTime,
          targetCalories: result.targetCalories,
          proteinG: result.proteinG,
          fatG: result.fatG,
          carbG: result.carbG,
        }),
      });
      if (!res.ok) throw new Error("failed");
      const data = (await res.json()) as MealPlan;
      setPlan(data);
      setState("done");
    } catch {
      setState("error");
    }
  }

  if (state === "idle" || state === "error") {
    return (
      <div className="space-y-2">
        <Button className="w-full" onClick={generate}>
          AI 추천 식단 보기
        </Button>
        {state === "error" && (
          <p className="text-sm text-destructive">식단 생성에 실패했습니다. 다시 시도해주세요.</p>
        )}
      </div>
    );
  }

  if (state === "loading") {
    return (
      <Button className="w-full" disabled>
        식단 생성 중...
      </Button>
    );
  }

  if (!plan) return null;

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">{plan.summary}</p>
      <div className="space-y-2">
        {plan.meals.map((meal, i) => (
          <div key={i} className="rounded-lg border p-3 space-y-1">
            <div className="flex items-center justify-between">
              <Badge variant="secondary">{SLOT_LABEL[meal.slot]}</Badge>
              <span className="text-xs text-muted-foreground tabular-nums">
                약 {meal.estimatedCalories}kcal
              </span>
            </div>
            <p className="text-sm font-medium">{meal.menu}</p>
            <p className="text-xs text-muted-foreground">{meal.items.join(" · ")}</p>
          </div>
        ))}
      </div>
      {plan.tips.length > 0 && (
        <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
          {plan.tips.map((tip, i) => (
            <li key={i}>{tip}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
