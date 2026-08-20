export type Gender = "male" | "female";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "very_active";
export type Goal = "lose" | "maintain" | "gain" | "muscle_gain";

export const ACTIVITY_MULTIPLIER: Record<ActivityLevel, number> = {
  sedentary: 1.2,
  light: 1.375,
  moderate: 1.55,
  active: 1.725,
  very_active: 1.9,
};

export const ACTIVITY_LABEL: Record<ActivityLevel, string> = {
  sedentary: "거의 운동 안 함 (주로 앉아서 생활)",
  light: "가벼운 활동 (주 1~3회 가벼운 운동)",
  moderate: "보통 활동 (주 3~5회 운동)",
  active: "활발한 활동 (주 6~7회 운동)",
  very_active: "매우 활발함 (매일 강도 높은 운동/육체노동)",
};

export const GOAL_LABEL: Record<Goal, string> = {
  lose: "체중 감량",
  maintain: "체중 유지",
  gain: "체중 증량",
  muscle_gain: "근육량 증가",
};

export interface NutritionInput {
  gender: Gender;
  age: number;
  heightCm: number;
  weightKg: number;
  activity: ActivityLevel;
  goal: Goal;
}

export interface NutritionResult {
  bmr: number;
  tdee: number;
  targetCalories: number;
  proteinG: number;
  fatG: number;
  carbG: number;
}

/** Mifflin-St Jeor 공식 기반 기초대사량(BMR) */
export function calcBMR({ gender, age, heightCm, weightKg }: Pick<NutritionInput, "gender" | "age" | "heightCm" | "weightKg">): number {
  const base = 10 * weightKg + 6.25 * heightCm - 5 * age;
  return gender === "male" ? base + 5 : base - 161;
}

const GOAL_CALORIE_ADJUSTMENT: Record<Goal, number> = {
  lose: -500,
  maintain: 0,
  gain: 300,
  muscle_gain: 200,
};

const GOAL_PROTEIN_PER_KG: Record<Goal, number> = {
  lose: 1.8,
  maintain: 1.4,
  gain: 1.6,
  muscle_gain: 2.0,
};

export function calcNutrition(input: NutritionInput): NutritionResult {
  const bmr = calcBMR(input);
  const tdee = bmr * ACTIVITY_MULTIPLIER[input.activity];
  const targetCalories = Math.max(1200, Math.round(tdee + GOAL_CALORIE_ADJUSTMENT[input.goal]));

  const proteinG = Math.round(input.weightKg * GOAL_PROTEIN_PER_KG[input.goal]);
  const proteinCal = proteinG * 4;

  const fatCal = targetCalories * 0.25;
  const fatG = Math.round(fatCal / 9);

  const carbCal = Math.max(0, targetCalories - proteinCal - fatCal);
  const carbG = Math.round(carbCal / 4);

  return {
    bmr: Math.round(bmr),
    tdee: Math.round(tdee),
    targetCalories,
    proteinG,
    fatG,
    carbG,
  };
}
