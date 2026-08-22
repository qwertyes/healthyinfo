import { createGoogle } from "@ai-sdk/google";
import { generateText, Output } from "ai";
import { NextResponse } from "next/server";
import {
  MEAL_PLAN_SYSTEM_PROMPT,
  MealSchema,
  buildRegenerateMealPrompt,
  type RegenerateMealInput,
} from "@/lib/meal-plan";

const google = createGoogle({ apiKey: process.env.GEMINI_API_KEY });

export async function POST(request: Request) {
  const body = (await request.json()) as Partial<RegenerateMealInput>;

  if (
    !body.goal ||
    !body.dietType ||
    !body.slot ||
    typeof body.targetMealCalories !== "number"
  ) {
    return NextResponse.json({ error: "필수 값이 누락되었습니다." }, { status: 400 });
  }

  const input: RegenerateMealInput = {
    goal: body.goal,
    dietType: body.dietType,
    allergies: body.allergies ?? [],
    cookingTime: body.cookingTime ?? "",
    targetCalories: body.targetCalories ?? body.targetMealCalories,
    proteinG: body.proteinG ?? 0,
    fatG: body.fatG ?? 0,
    carbG: body.carbG ?? 0,
    slot: body.slot,
    targetMealCalories: body.targetMealCalories,
    exclude: body.exclude ?? [],
  };

  try {
    const { output } = await generateText({
      model: google("gemini-3.1-flash-lite"),
      system: MEAL_PLAN_SYSTEM_PROMPT,
      prompt: buildRegenerateMealPrompt(input),
      output: Output.object({ schema: MealSchema }),
    });

    return NextResponse.json(output);
  } catch (error) {
    console.error("meal regeneration failed", error);
    return NextResponse.json({ error: "메뉴 재생성에 실패했습니다. 잠시 후 다시 시도해주세요." }, { status: 502 });
  }
}
