import { z } from "zod";

export const MealSchema = z.object({
  slot: z.enum(["breakfast", "lunch", "dinner", "snack"]).describe("끼니 구분"),
  menu: z.string().describe("메뉴 이름"),
  items: z.array(z.string()).describe("구성 음식/재료 목록"),
  estimatedCalories: z.number().describe("이 끼니의 예상 칼로리(kcal)"),
});

export type Meal = z.infer<typeof MealSchema>;

export const MealPlanSchema = z.object({
  summary: z.string().describe("이 식단의 한 줄 요약 (예: 저탄고지 기반 체중 감량 식단)"),
  meals: z
    .array(MealSchema)
    .min(2)
    .max(5)
    .describe("하루 식단 구성. 간헐적 단식이면 끼니 수를 줄이는 등 diet_type을 반영"),
  tips: z
    .array(z.string())
    .min(1)
    .max(4)
    .describe("실천 팁 (최대 4개). 의학적 효과를 단정하는 표현 금지"),
});

export type MealPlan = z.infer<typeof MealPlanSchema>;

export const MEAL_PLAN_SYSTEM_PROMPT = `당신은 한끼정답 서비스의 식단 추천 AI입니다.
아래 규칙을 반드시 지키세요:

1. 특정 질병의 예방, 치료, 완치를 단정하지 마세요.
2. "치료", "처방", "주치의" 등 의료 행위를 암시하는 단어를 쓰지 마세요.
3. 특정 식품·영양제와 질병 효능을 직접 연결하지 마세요.
4. 사용자가 입력한 알레르기/못 먹는 음식은 어떤 메뉴에도 절대 포함하지 마세요.
5. 사용자가 선택한 선호 식단 유형(diet_type)을 반드시 반영하세요.
6. 각 끼니의 예상 칼로리 합이 사용자의 하루 목표 칼로리에서 크게 벗어나지 않도록 하세요 (±10% 이내).
7. 한국인이 실제로 구하기 쉬운 재료와 메뉴로 구성하세요.
8. tips는 실천 팁으로 작성하고, 의학적 효과를 단정하는 표현은 쓰지 마세요.`;

export interface MealPlanRequestInput {
  goal: string;
  dietType: string;
  allergies: string[];
  cookingTime: string;
  targetCalories: number;
  proteinG: number;
  fatG: number;
  carbG: number;
}

export function buildMealPlanPrompt(input: MealPlanRequestInput): string {
  return [
    `목표: ${input.goal}`,
    `선호 식단 유형: ${input.dietType}`,
    `알레르기/제외 음식: ${input.allergies.length > 0 ? input.allergies.join(", ") : "없음"}`,
    `요리 가능 시간: ${input.cookingTime}`,
    `하루 목표 칼로리: ${input.targetCalories}kcal`,
    `목표 영양소: 단백질 ${input.proteinG}g, 지방 ${input.fatG}g, 탄수화물 ${input.carbG}g`,
    "",
    "위 조건에 맞는 하루 식단을 추천해줘.",
  ].join("\n");
}

const SLOT_KOREAN: Record<Meal["slot"], string> = {
  breakfast: "아침",
  lunch: "점심",
  dinner: "저녁",
  snack: "간식",
};

export interface RegenerateMealInput extends MealPlanRequestInput {
  slot: Meal["slot"];
  targetMealCalories: number;
  exclude: string[];
}

export function buildRegenerateMealPrompt(input: RegenerateMealInput): string {
  return [
    `목표: ${input.goal}`,
    `선호 식단 유형: ${input.dietType}`,
    `알레르기/제외 음식: ${input.allergies.length > 0 ? input.allergies.join(", ") : "없음"}`,
    `요리 가능 시간: ${input.cookingTime}`,
    `이 끼니(${SLOT_KOREAN[input.slot]})의 목표 칼로리: 약 ${input.targetMealCalories}kcal`,
    input.exclude.length > 0
      ? `이미 제안했던 메뉴라 이번엔 피해야 할 메뉴: ${input.exclude.join(", ")}`
      : "",
    "",
    `위 조건에 맞는 "${SLOT_KOREAN[input.slot]}" 메뉴 하나만 새로 추천해줘. 방금 제외 목록에 있는 것과는 다른 메뉴여야 해.`,
  ]
    .filter(Boolean)
    .join("\n");
}
