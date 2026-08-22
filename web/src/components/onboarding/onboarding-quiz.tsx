"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { DisclaimerNote } from "@/components/disclaimer-note";
import { MealPlanPanel } from "@/components/onboarding/meal-plan-panel";
import { supabase } from "@/lib/supabase/client";
import type { MealPlan } from "@/lib/meal-plan";
import {
  ACTIVITY_LABEL,
  GOAL_LABEL,
  calcNutrition,
  type ActivityLevel,
  type Gender,
  type Goal,
} from "@/lib/nutrition";
import {
  COMMON_ALLERGENS,
  COOKING_TIME_LABEL,
  DEFAULT_ANSWERS,
  DIET_TYPE_LABEL,
  deriveProfileLabel,
  type CookingTime,
  type DietType,
  type QuizAnswers,
} from "@/lib/quiz";

const TOTAL_STEPS = 6;

export function OnboardingQuiz() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<QuizAnswers>(DEFAULT_ANSWERS);
  const [done, setDone] = useState(false);
  const [email, setEmail] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [aiPlan, setAiPlan] = useState<MealPlan | null>(null);
  const [savedId, setSavedId] = useState<string | null>(null);

  function update<K extends keyof QuizAnswers>(key: K, value: QuizAnswers[K]) {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  }

  function toggleAllergen(name: string) {
    setAnswers((prev) => ({
      ...prev,
      allergies: prev.allergies.includes(name)
        ? prev.allergies.filter((a) => a !== name)
        : [...prev.allergies, name],
    }));
  }

  const canProceed = (() => {
    switch (step) {
      case 1:
        return Boolean(answers.age && answers.heightCm && answers.weightKg);
      default:
        return true;
    }
  })();

  function next() {
    if (step === TOTAL_STEPS - 1) {
      setDone(true);
      return;
    }
    setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));
  }

  function back() {
    if (done) {
      setDone(false);
      return;
    }
    setStep((s) => Math.max(s - 1, 0));
  }

  if (done) {
    const result = calcNutrition({
      gender: answers.gender,
      age: Number(answers.age),
      heightCm: Number(answers.heightCm),
      weightKg: Number(answers.weightKg),
      activity: answers.activity,
      goal: answers.goal,
    });
    const profile = deriveProfileLabel(answers);

    async function saveSubmission() {
      setSaveState("saving");
      const { data, error } = await supabase
        .from("onboarding_submissions")
        .insert({
          email: email || null,
          goal: answers.goal,
          gender: answers.gender,
          age: Number(answers.age),
          height_cm: Number(answers.heightCm),
          weight_kg: Number(answers.weightKg),
          activity: answers.activity,
          allergies: answers.allergies,
          diet_type: answers.dietType,
          has_condition: answers.hasCondition,
          condition_note: answers.conditionNote || null,
          cooking_time: answers.cookingTime,
          bmr: result.bmr,
          tdee: result.tdee,
          target_calories: result.targetCalories,
          protein_g: result.proteinG,
          fat_g: result.fatG,
          carb_g: result.carbG,
          meal_plan: aiPlan,
        })
        .select("id")
        .single();
      if (error) {
        setSaveState("error");
        return;
      }
      setSavedId(data.id);
      setSaveState("saved");
    }

    return (
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
              하루 목표 {result.targetCalories.toLocaleString()} kcal
            </p>
            <div className="grid grid-cols-3 gap-2 text-sm tabular-nums">
              <div className="rounded-md bg-background p-2 text-center">
                <div className="text-muted-foreground text-xs">단백질</div>
                <div className="font-medium">{result.proteinG}g</div>
              </div>
              <div className="rounded-md bg-background p-2 text-center">
                <div className="text-muted-foreground text-xs">지방</div>
                <div className="font-medium">{result.fatG}g</div>
              </div>
              <div className="rounded-md bg-background p-2 text-center">
                <div className="text-muted-foreground text-xs">탄수화물</div>
                <div className="font-medium">{result.carbG}g</div>
              </div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <p>
              <span className="text-muted-foreground">선호 식단</span>{" "}
              <Badge variant="secondary">{DIET_TYPE_LABEL[answers.dietType]}</Badge>
            </p>
            {answers.allergies.length > 0 && (
              <p>
                <span className="text-muted-foreground">제외 식재료</span>{" "}
                {answers.allergies.map((a) => (
                  <Badge key={a} variant="outline" className="mr-1">
                    {a}
                  </Badge>
                ))}
              </p>
            )}
            {answers.hasCondition && (
              <p className="text-muted-foreground">
                입력하신 건강 상태는 식단 제안 시 참고용으로만 사용되며, 진단이나 처방이 아닙니다.
              </p>
            )}
          </div>

          <MealPlanPanel answers={answers} result={result} onPlanGenerated={setAiPlan} />

          <DisclaimerNote />

          {saveState === "saved" && savedId ? (
            <div className="space-y-2 rounded-lg border bg-muted/40 p-4 text-center text-sm">
              <p>결과가 저장되었습니다. 이 링크로 언제든 다시 볼 수 있어요.</p>
              <Link
                href={`/plan/${savedId}`}
                className="inline-block font-medium text-brand hover:underline"
              >
                내 결과 다시 보기 →
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="q-email">이메일 (선택)</Label>
              <Input
                id="q-email"
                type="email"
                placeholder="결과를 이메일로 받아보고 싶다면 입력하세요"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              {saveState === "error" && (
                <p className="text-sm text-destructive">저장에 실패했습니다. 다시 시도해주세요.</p>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <Button variant="outline" onClick={back}>
              다시 보기
            </Button>
            {saveState !== "saved" && (
              <Button className="flex-1" onClick={saveSubmission} disabled={saveState === "saving"}>
                {saveState === "saving" ? "저장 중..." : "결과 저장하기"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-xl">
      <CardHeader className="space-y-3">
        <Progress value={((step + 1) / TOTAL_STEPS) * 100} />
        <CardTitle>
          {step + 1} / {TOTAL_STEPS}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {step === 0 && (
          <div className="space-y-3">
            <Label>목표가 무엇인가요?</Label>
            <div className="grid grid-cols-2 gap-2">
              {(Object.entries(GOAL_LABEL) as [Goal, string][]).map(([value, label]) => (
                <Button
                  key={value}
                  type="button"
                  variant={answers.goal === value ? "default" : "outline"}
                  onClick={() => update("goal", value)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <div className="flex gap-2">
              {(["female", "male"] as Gender[]).map((g) => (
                <Button
                  key={g}
                  type="button"
                  variant={answers.gender === g ? "default" : "outline"}
                  className="flex-1"
                  onClick={() => update("gender", g)}
                >
                  {g === "female" ? "여성" : "남성"}
                </Button>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="q-age">나이</Label>
                <Input id="q-age" type="number" value={answers.age} onChange={(e) => update("age", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="q-height">키(cm)</Label>
                <Input id="q-height" type="number" value={answers.heightCm} onChange={(e) => update("heightCm", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="q-weight">체중(kg)</Label>
                <Input id="q-weight" type="number" value={answers.weightKg} onChange={(e) => update("weightKg", e.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>활동량</Label>
              <div className="grid gap-2">
                {(Object.entries(ACTIVITY_LABEL) as [ActivityLevel, string][]).map(([value, label]) => (
                  <Button
                    key={value}
                    type="button"
                    variant={answers.activity === value ? "default" : "outline"}
                    className="justify-start"
                    onClick={() => update("activity", value)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <Label>알레르기 / 못 먹는 음식이 있나요?</Label>
            <p className="text-sm text-muted-foreground">추천 식단에서 자동으로 제외됩니다.</p>
            <div className="grid grid-cols-2 gap-3">
              {COMMON_ALLERGENS.map((name) => (
                <label key={name} className="flex items-center gap-2 text-sm">
                  <Checkbox
                    checked={answers.allergies.includes(name)}
                    onCheckedChange={() => toggleAllergen(name)}
                  />
                  {name}
                </label>
              ))}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <Label>선호하는 식단 유형이 있나요?</Label>
            <div className="grid grid-cols-2 gap-2">
              {(Object.entries(DIET_TYPE_LABEL) as [DietType, string][]).map(([value, label]) => (
                <Button
                  key={value}
                  type="button"
                  variant={answers.dietType === value ? "default" : "outline"}
                  onClick={() => update("dietType", value)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <Label>기저질환이 있으신가요? (선택)</Label>
                <p className="text-sm text-muted-foreground">
                  당뇨, 고혈압 등. 입력하지 않아도 서비스 이용에 문제없습니다.
                </p>
              </div>
              <Switch checked={answers.hasCondition} onCheckedChange={(v) => update("hasCondition", v)} />
            </div>
            {answers.hasCondition && (
              <div className="space-y-1.5">
                <Textarea
                  placeholder="예: 고혈압 약 복용 중"
                  value={answers.conditionNote}
                  onChange={(e) => update("conditionNote", e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  이 정보는 맞춤 식단 제안의 참고용으로만 사용되며, 안전하게 저장·처리됩니다.
                </p>
              </div>
            )}
          </div>
        )}

        {step === 5 && (
          <div className="space-y-3">
            <Label>하루에 요리할 수 있는 시간은 어느 정도인가요?</Label>
            <div className="grid gap-2">
              {(Object.entries(COOKING_TIME_LABEL) as [CookingTime, string][]).map(([value, label]) => (
                <Button
                  key={value}
                  type="button"
                  variant={answers.cookingTime === value ? "default" : "outline"}
                  className="justify-start"
                  onClick={() => update("cookingTime", value)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2 pt-2">
          {step > 0 && (
            <Button variant="outline" onClick={back}>
              이전
            </Button>
          )}
          <Button className="flex-1" onClick={next} disabled={!canProceed}>
            {step === TOTAL_STEPS - 1 ? "결과 보기" : "다음"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
