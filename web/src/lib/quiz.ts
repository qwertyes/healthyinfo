import type { ActivityLevel, Gender, Goal } from "@/lib/nutrition";

export type DietType = "general" | "low_carb" | "vegan" | "intermittent_fasting";

export const DIET_TYPE_LABEL: Record<DietType, string> = {
  general: "일반식",
  low_carb: "저탄고지",
  vegan: "비건/채식",
  intermittent_fasting: "간헐적 단식",
};

export const COMMON_ALLERGENS = [
  "달걀",
  "우유",
  "땅콩",
  "갑각류",
  "밀/글루텐",
  "대두",
] as const;

export type CookingTime = "low" | "medium" | "high";

export const COOKING_TIME_LABEL: Record<CookingTime, string> = {
  low: "거의 없음 (간편식 위주)",
  medium: "보통 (하루 20~30분)",
  high: "충분함 (직접 요리 선호)",
};

export interface QuizAnswers {
  goal: Goal;
  gender: Gender;
  age: string;
  heightCm: string;
  weightKg: string;
  activity: ActivityLevel;
  allergies: string[];
  dietType: DietType;
  hasCondition: boolean;
  conditionNote: string;
  cookingTime: CookingTime;
}

export const DEFAULT_ANSWERS: QuizAnswers = {
  goal: "lose",
  gender: "female",
  age: "",
  heightCm: "",
  weightKg: "",
  activity: "light",
  allergies: [],
  dietType: "general",
  hasCondition: false,
  conditionNote: "",
  cookingTime: "medium",
};

const PROFILE_BY_GOAL: Record<Goal, string> = {
  lose: "체중 감량 집중형",
  maintain: "현상 유지형",
  gain: "체중 증량형",
  muscle_gain: "근육량 증가 집중형",
};

const PROFILE_BY_COOKING: Record<CookingTime, string> = {
  low: "간편식 활용형",
  medium: "균형 조리형",
  high: "직접 조리 선호형",
};

/** 온보딩 결과 리포트에 쓰는 "식습관 유형" 라벨 (Noom 패턴 참고).
 * /plan/[id]처럼 DB에서 goal/cookingTime만 읽어온 경우에도 재사용할 수 있도록 필요한
 * 필드만 받는다. */
export function deriveProfileLabel(answers: Pick<QuizAnswers, "goal" | "cookingTime">): string {
  return `${PROFILE_BY_GOAL[answers.goal]} · ${PROFILE_BY_COOKING[answers.cookingTime]}`;
}
