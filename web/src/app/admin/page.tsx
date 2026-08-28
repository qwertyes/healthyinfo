import { notFound } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { createClient } from "@/lib/supabase/server";

const ADMIN_EMAIL = "silvernatural2@gmail.com";

interface Member {
  email: string | null;
  provider: string;
  created_at: string;
}

interface ViewStats {
  total_views: number;
  unique_days: number;
  last_7_days: number;
}

export const metadata = {
  title: "관리자 — 한끼정답",
};

export default async function AdminPage() {
  const supabase = await createClient();
  const { data: userData } = await supabase.auth.getUser();

  if (!userData.user || userData.user.email !== ADMIN_EMAIL) {
    notFound();
  }

  const [{ data: membersData, error: membersError }, { data: statsData, error: statsError }] = await Promise.all([
    supabase.rpc("admin_list_members"),
    supabase.rpc("admin_page_view_stats"),
  ]);

  const members = membersData as Member[] | null;
  const stats = (statsData as ViewStats[] | null)?.[0];

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16">
      <div className="w-full max-w-3xl space-y-8">
        <h1 className="font-heading text-2xl tracking-tight">관리자</h1>

        <div className="grid grid-cols-3 gap-3">
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-medium text-muted-foreground">전체 방문</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold tabular-nums">{stats?.total_views ?? "—"}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-medium text-muted-foreground">최근 7일</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold tabular-nums">{stats?.last_7_days ?? "—"}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-xs font-medium text-muted-foreground">방문 있었던 일수</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold tabular-nums">{stats?.unique_days ?? "—"}</p>
            </CardContent>
          </Card>
        </div>
        {statsError && (
          <p className="text-sm text-destructive">방문 통계를 불러오지 못했습니다: {statsError.message}</p>
        )}

        <Card>
          <CardHeader>
            <CardTitle>
              회원 목록 <span className="font-normal text-muted-foreground">({members?.length ?? 0}명)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {membersError && (
              <p className="text-sm text-destructive">회원 목록을 불러오지 못했습니다: {membersError.message}</p>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">이메일</th>
                    <th className="py-2 pr-4 font-medium">가입 경로</th>
                    <th className="py-2 font-medium">가입일</th>
                  </tr>
                </thead>
                <tbody>
                  {(members ?? []).map((m, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2 pr-4">{m.email ?? <span className="text-muted-foreground">(이메일 없음)</span>}</td>
                      <td className="py-2 pr-4">
                        <Badge variant="secondary">{m.provider}</Badge>
                      </td>
                      <td className="py-2 tabular-nums">
                        {new Date(m.created_at).toLocaleDateString("ko-KR", {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(members ?? []).length === 0 && !membersError && (
                <p className="py-6 text-center text-sm text-muted-foreground">아직 가입한 회원이 없습니다.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
