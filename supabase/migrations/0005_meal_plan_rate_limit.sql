-- 무료 사용자의 AI 식단 생성(초기 생성 + 끼니 재생성 합산)을 하루 3회로 제한한다.
-- 로그인 전이라 사용자 식별이 안 되므로 우선 IP 해시로 제한(개인정보 보호를 위해 원본 IP는
-- 저장하지 않고 sha256 해시만 저장). 로그인 붙으면 user_id 기준으로 바꿀 수 있다.
create table if not exists meal_plan_usage (
  ip_hash text not null,
  usage_date date not null default current_date,
  count integer not null default 0,
  primary key (ip_hash, usage_date)
);

alter table meal_plan_usage enable row level security;
-- 정책을 하나도 안 붙여서 anon/authenticated로는 테이블에 직접 접근 불가 —
-- 아래 SECURITY DEFINER 함수를 통해서만 증가/조회 가능.

create or replace function check_meal_plan_quota(p_ip_hash text, p_limit integer default 3)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  current_count integer;
begin
  insert into meal_plan_usage (ip_hash, usage_date, count)
  values (p_ip_hash, current_date, 0)
  on conflict (ip_hash, usage_date) do nothing;

  select count into current_count
  from meal_plan_usage
  where ip_hash = p_ip_hash and usage_date = current_date
  for update;

  if current_count >= p_limit then
    return -1;
  end if;

  update meal_plan_usage
  set count = count + 1
  where ip_hash = p_ip_hash and usage_date = current_date;

  return current_count + 1;
end;
$$;

grant execute on function check_meal_plan_quota(text, integer) to anon, authenticated;
