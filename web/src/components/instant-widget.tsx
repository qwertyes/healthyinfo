"use client";

import { useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DisclaimerNote } from "@/components/disclaimer-note";
import {
  ACTIVITY_LABEL,
  GOAL_LABEL,
  calcNutrition,
  type ActivityLevel,
  type Gender,
  type Goal,
  type NutritionResult,
} from "@/lib/nutrition";
import Link from "next/link";

const ACTIVITY_OPTIONS = Object.entries(ACTIVITY_LABEL) as [ActivityLevel, string][];
const GOAL_OPTIONS = Object.entries(GOAL_LABEL) as [Goal, string][];

export function InstantWidget() {
  const [gender, setGender] = useState<Gender>("female");
  const [age, setAge] = useState("28");
  const [height, setHeight] = useState("165");
  const [weight, setWeight] = useState("58");
  const [activity, setActivity] = useState<ActivityLevel>("light");
  const [goal, setGoal] = useState<Goal>("lose");
  const [result, setResult] = useState<NutritionResult | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const ageNum = Number(age);
    const heightNum = Number(height);
    const weightNum = Number(weight);
    if (!ageNum || !heightNum || !weightNum) return;

    setResult(
      calcNutrition({
        gender,
        age: ageNum,
        heightCm: heightNum,
        weightKg: weightNum,
        activity,
        goal,
      })
    );
  }

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>30초 만에 내 하루 식단 목표 확인하기</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
          <div className="col-span-2 flex gap-2">
            {(["female", "male"] as Gender[]).map((g) => (
              <Button
                key={g}
                type="button"
                variant={gender === g ? "default" : "outline"}
                className="flex-1"
                onClick={() => setGender(g)}
              >
                {g === "female" ? "여성" : "남성"}
              </Button>
            ))}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="age">나이</Label>
            <Input id="age" type="number" inputMode="numeric" min={10} max={100} value={age} onChange={(e) => setAge(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="height">키 (cm)</Label>
            <Input id="height" type="number" inputMode="numeric" min={100} max={230} value={height} onChange={(e) => setHeight(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="weight">체중 (kg)</Label>
            <Input id="weight" type="number" inputMode="numeric" min={30} max={200} value={weight} onChange={(e) => setWeight(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>목표</Label>
            <Select value={goal} onValueChange={(v) => setGoal(v as Goal)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {GOAL_OPTIONS.map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="col-span-2 space-y-1.5">
            <Label>활동량</Label>
            <Select value={activity} onValueChange={(v) => setActivity(v as ActivityLevel)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ACTIVITY_OPTIONS.map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" className="col-span-2">
            지금 바로 확인하기
          </Button>
        </form>

        {result && (
          <div className="rounded-lg border bg-muted/40 p-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              기초대사량 <strong className="text-foreground">{result.bmr.toLocaleString()} kcal</strong> · 활동
              대사량 <strong className="text-foreground">{result.tdee.toLocaleString()} kcal</strong>
            </p>
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
            <Link href="/onboarding" className={buttonVariants({ className: "w-full" })}>
              저장하고 맞춤 식단 더 받아보기
            </Link>
          </div>
        )}

        <DisclaimerNote />
      </CardContent>
    </Card>
  );
}
