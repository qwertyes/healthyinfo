"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
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
  const [showTodayForm, setShowTodayForm] = useState(false);
  const [todayNote, setTodayNote] = useState("");
  const [todayLoading, setTodayLoading] = useState(false);
  const [todayError, setTodayError] = useState<string | null>(null);

  async function requestPlan(todayNoteValue?: string) {
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
        todayNote: todayNoteValue,
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.error ?? "식단 생성에 실패했습니다. 다시 시도해주세요.");
    }
    return (await res.json()) as MealPlan;
  }

  async function generate() {
    setState("loading");
    try {
      const data = await requestPlan();
      setPlan(data);
      setState("done");
      onPlanGenerated?.(data);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "식단 생성에 실패했습니다. 다시 시도해주세요.");
      setState("error");
    }
  }

  async function regenerateToday() {
    setTodayLoading(true);
    setTodayError(null);
    try {
      const data = await requestPlan(todayNote.trim() || undefined);
      setPlan(data);
      setShowTodayForm(false);
      setTodayNote("");
      onPlanGenerated?.(data);
    } catch (err) {
      // 실패해도 기존 식단은 그대로 둔다 — 처음부터 다시 만들라고 강요하지 않는다.
      setTodayError(err instanceof Error ? err.message : "다시 만들기에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setTodayLoading(false);
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
    <div className="space-y-3">
      <MealPlanDisplay plan={plan} onRegenerate={regenerateMeal} regeneratingIndex={regeneratingIndex} />
      {regenerateError && <p className="text-sm text-destructive">{regenerateError}</p>}

      <div className="rounded-lg border border-dashed p-3 space-y-2">
        {!showTodayForm ? (
          <Button variant="ghost" size="sm" className="w-full" onClick={() => setShowTodayForm(true)}>
            오늘 컨디션 반영해서 다시 받기
          </Button>
        ) : (
          <div className="space-y-2">
            <Textarea
              placeholder="예: 어제 과식했어요 / 오늘은 매운 음식이 당겨요 (선택)"
              value={todayNote}
              onChange={(e) => setTodayNote(e.target.value)}
              disabled={todayLoading}
              className="text-sm"
            />
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowTodayForm(false)} disabled={todayLoading}>
                취소
              </Button>
              <Button size="sm" className="flex-1" onClick={regenerateToday} disabled={todayLoading}>
                {todayLoading ? "다시 만드는 중..." : "오늘 식단 다시 만들기"}
              </Button>
            </div>
            {todayError && <p className="text-sm text-destructive">{todayError}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
