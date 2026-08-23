"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { DIET_TYPE_LABEL, type QuizAnswers } from "@/lib/quiz";
import { GOAL_LABEL, type NutritionResult } from "@/lib/nutrition";
import type { Meal, MealPlan } from "@/lib/meal-plan";
import { MealPlanDisplay } from "@/components/onboarding/meal-plan-display";

export function MealPlanPanel({
  answers,
  result,
  onPlanGenerated,
}: {
  answers: QuizAnswers;
  result: NutritionResult;
  onPlanGenerated?: (plan: MealPlan) => void;
}) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);

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
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.error ?? "식단 생성에 실패했습니다. 다시 시도해주세요.");
      }
      const data = (await res.json()) as MealPlan;
      setPlan(data);
      setState("done");
      onPlanGenerated?.(data);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "식단 생성에 실패했습니다. 다시 시도해주세요.");
      setState("error");
    }
  }

  async function regenerateMeal(index: number) {
    if (!plan) return;
    const target = plan.meals[index];
    setRegeneratingIndex(index);
    setRegenerateError(null);
    try {
      const res = await fetch("/api/meal-plan/regenerate", {
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
          slot: target.slot,
          targetMealCalories: target.estimatedCalories,
          exclude: plan.meals.map((m) => m.menu),
        }),
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => null);
        throw new Error(errBody?.error ?? "메뉴 재생성에 실패했습니다. 다시 시도해주세요.");
      }
      const newMeal = (await res.json()) as Meal;
      const nextMeals = plan.meals.map((m, i) => (i === index ? { ...newMeal, slot: target.slot } : m));
      const nextPlan = { ...plan, meals: nextMeals };
      setPlan(nextPlan);
      onPlanGenerated?.(nextPlan);
    } catch (err) {
      // 실패해도 기존 메뉴는 그대로 둔다 — 메시지만 보여주고 버튼 상태를 원복.
      setRegenerateError(err instanceof Error ? err.message : "메뉴 재생성에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setRegeneratingIndex(null);
    }
  }

  if (state === "idle" || state === "error") {
    return (
      <div className="space-y-2">
        <Button className="w-full" onClick={generate}>
          AI 추천 식단 보기
        </Button>
        {state === "error" && errorMessage && (
          <p className="text-sm text-destructive">{errorMessage}</p>
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
    <div className="space-y-2">
      <MealPlanDisplay plan={plan} onRegenerate={regenerateMeal} regeneratingIndex={regeneratingIndex} />
      {regenerateError && <p className="text-sm text-destructive">{regenerateError}</p>}
    </div>
  );
}
