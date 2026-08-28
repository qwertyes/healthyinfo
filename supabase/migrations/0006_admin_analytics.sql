-- 관리자 전용 페이지(회원 목록 + 방문 통계)를 위한 최소 구조.
-- 페이지뷰는 익명 요청도 기록해야 하므로 INSERT만 열어두고(개인정보 없음, path만 저장),
-- 조회는 아래 SECURITY DEFINER 함수를 통해 관리자 이메일로 로그인했을 때만 가능하다.
create table if not exists page_views (
  id bigint generated always as identity primary key,
  path text not null,
  created_at timestamptz not null default now()
);

alter table page_views enable row level security;

create policy "누구나 페이지뷰 기록 가능"
  on page_views for insert
  to anon, authenticated
  with check (true);
-- select/update/delete 정책 없음 — 직접 조회는 anon/authenticated 둘 다 불가.

create or replace function admin_list_members()
returns table(email text, provider text, created_at timestamptz)
language plpgsql
security definer
set search_path = public, auth
as $$
begin
  if auth.email() is distinct from 'silvernatural2@gmail.com' then
    raise exception 'unauthorized';
  end if;

  return query
    select
      u.email,
      coalesce(u.raw_app_meta_data->>'provider', 'email') as provider,
      u.created_at
    from auth.users u
    order by u.created_at desc;
end;
$$;

grant execute on function admin_list_members() to authenticated;

create or replace function admin_page_view_stats()
returns table(total_views bigint, unique_days bigint, last_7_days bigint)
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.email() is distinct from 'silvernatural2@gmail.com' then
    raise exception 'unauthorized';
  end if;

  return query
    select
      count(*)::bigint as total_views,
      count(distinct date(created_at))::bigint as unique_days,
      count(*) filter (where created_at > now() - interval '7 days')::bigint as last_7_days
    from page_views;
end;
$$;

grant execute on function admin_page_view_stats() to authenticated;
