import { createGoogle } from "@ai-sdk/google";
import { generateText, Output } from "ai";
import { NextResponse } from "next/server";
import {
  MEAL_PLAN_SYSTEM_PROMPT,
  MealPlanSchema,
  buildMealPlanPrompt,
  type MealPlanRequestInput,
} from "@/lib/meal-plan";

// my-video-creator와 동일한 env var 이름(GEMINI_API_KEY)을 그대로 사용
const google = createGoogle({ apiKey: process.env.GEMINI_API_KEY });

export async function POST(request: Request) {
  const body = (await request.json()) as Partial<MealPlanRequestInput>;

  if (
    !body.goal ||
    !body.dietType ||
    !body.cookingTime ||
    typeof body.targetCalories !== "number" ||
    typeof body.proteinG !== "number" ||
    typeof body.fatG !== "number" ||
    typeof body.carbG !== "number"
  ) {
    return NextResponse.json({ error: "필수 값이 누락되었습니다." }, { status: 400 });
  }

  const input: MealPlanRequestInput = {
    goal: body.goal,
    dietType: body.dietType,
    allergies: body.allergies ?? [],
    cookingTime: body.cookingTime,
    targetCalories: body.targetCalories,
    proteinG: body.proteinG,
    fatG: body.fatG,
    carbG: body.carbG,
  };

  try {
    const { output } = await generateText({
      // my-video-creator와 동일한 모델(가장 저렴한 flash-lite 티어)
      model: google("gemini-3.1-flash-lite"),
      system: MEAL_PLAN_SYSTEM_PROMPT,
      prompt: buildMealPlanPrompt(input),
      output: Output.object({ schema: MealPlanSchema }),
    });

    return NextResponse.json(output);
  } catch (error) {
    console.error("meal-plan generation failed", error);
    return NextResponse.json({ error: "식단 생성에 실패했습니다. 잠시 후 다시 시도해주세요." }, { status: 502 });
  }
}
