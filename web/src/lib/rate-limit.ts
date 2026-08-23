import { createHash } from "crypto";
import { createClient } from "@supabase/supabase-js";

const DAILY_FREE_LIMIT = 3;

// 이 체크는 로그인 여부와 무관하게 익명 IP 기준으로 동작하므로, 세션 쿠키가 필요 없는
// 단순 서버 클라이언트로 충분하다 (브라우저용 SSR 클라이언트와 별개).
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
);

function getClientIp(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0].trim();
  return request.headers.get("x-real-ip") ?? "unknown";
}

function hashIp(ip: string): string {
  return createHash("sha256").update(ip).digest("hex");
}

export const MEAL_PLAN_QUOTA_MESSAGE = `오늘 무료 이용 횟수(${DAILY_FREE_LIMIT}회)를 모두 사용했어요. 내일 다시 시도해주세요.`;

export async function checkMealPlanQuota(request: Request): Promise<{ allowed: boolean }> {
  const ipHash = hashIp(getClientIp(request));
  const { data, error } = await supabase.rpc("check_meal_plan_quota", {
    p_ip_hash: ipHash,
    p_limit: DAILY_FREE_LIMIT,
  });

  if (error) {
    console.error("meal plan quota check failed", error);
    return { allowed: true };
  }

  return { allowed: data !== -1 };
}
