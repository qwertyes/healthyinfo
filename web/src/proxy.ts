import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;

// 로그인 세션 쿠키(sb-*)는 만료 시각이 있어서, 매 요청마다 여기서 갱신해줘야 서버
// 컴포넌트/라우트 핸들러가 오래된 세션을 보지 않는다 (Supabase SSR 공식 패턴).
export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(supabaseUrl, supabaseKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });

  await supabase.auth.getUser();

  // 방문 통계용 — 실제 페이지 이동(GET)만 집계, API 호출/폼 제출 등은 제외.
  if (request.method === "GET" && !request.nextUrl.pathname.startsWith("/api")) {
    try {
      await supabase.from("page_views").insert({ path: request.nextUrl.pathname });
    } catch {
      // 통계 기록 실패는 페이지 로드를 막을 이유가 안 됨 — 조용히 무시.
    }
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
