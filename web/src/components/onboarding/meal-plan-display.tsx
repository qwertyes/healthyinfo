import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { MealPlan } from "@/lib/meal-plan";

export const SLOT_LABEL: Record<MealPlan["meals"][number]["slot"], string> = {
  breakfast: "아침",
  lunch: "점심",
  dinner: "저녁",
  snack: "간식",
};

export function MealPlanDisplay({
  plan,
  onRegenerate,
  regeneratingIndex,
}: {
  plan: MealPlan;
  onRegenerate?: (index: number) => void;
  regeneratingIndex?: number | null;
}) {
  // 장보기 목록 — 끼니별 재료(items)를 모아서 중복 제거. 새 데이터 없이 이미 생성된
  // 식단에서 파생만 하면 되므로 별도 API 호출이 필요 없다.
  const groceryList = Array.from(new Set(plan.meals.flatMap((meal) => meal.items)));

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <p className="text-sm font-medium">{plan.summary}</p>
        <div className="space-y-2">
          {plan.meals.map((meal, i) => (
            <div key={i} className="rounded-lg border p-3 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <Badge variant="secondary">{SLOT_LABEL[meal.slot]}</Badge>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground tabular-nums">
                    약 {meal.estimatedCalories}kcal
                  </span>
                  {onRegenerate && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs text-brand hover:text-brand"
                      onClick={() => onRegenerate(i)}
                      disabled={regeneratingIndex === i}
                    >
                      {regeneratingIndex === i ? "바꾸는 중..." : "다른 메뉴로"}
                    </Button>
                  )}
                </div>
              </div>
              <p className="text-sm font-medium">{meal.menu}</p>
              <p className="text-xs text-muted-foreground">{meal.items.join(" · ")}</p>
            </div>
          ))}
        </div>
      </div>

      {groceryList.length > 0 && (
        <div className="space-y-2 rounded-lg border p-3">
          <p className="text-sm font-medium">장보기 목록</p>
          <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-muted-foreground">
            {groceryList.map((item) => (
              <li key={item}>· {item}</li>
            ))}
          </ul>
        </div>
      )}

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
