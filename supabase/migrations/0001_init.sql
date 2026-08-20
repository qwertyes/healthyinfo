-- 한끼정답 초기 스키마
-- 사용자(profiles), 온보딩 응답 + 식단 결과(onboarding_submissions)
-- Supabase SQL Editor에 붙여넣어 실행합니다.

-- 1) profiles: 향후 로그인(Supabase Auth) 붙일 때 쓸 사용자 프로필.
--    지금은 온보딩 퀴즈가 로그인 없이도 동작하므로 비어 있을 수 있음.
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "profiles: 본인만 조회" on public.profiles
  for select using (auth.uid() = id);

create policy "profiles: 본인만 수정" on public.profiles
  for update using (auth.uid() = id);

-- auth.users에 새 계정이 생기면 profiles 행을 자동 생성
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 2) onboarding_submissions: 온보딩 퀴즈 응답 + 계산된 식단 결과.
--    로그인 없이도(익명 사용자) 이메일만 선택 입력해서 저장 가능 (리드 캡처 패턴).
--    user_id는 나중에 로그인 기능이 붙으면 채워짐 — 지금은 대부분 NULL.
create table if not exists public.onboarding_submissions (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  user_id uuid references public.profiles (id) on delete set null,
  email text,

  -- 온보딩 응답
  goal text not null check (goal in ('lose', 'maintain', 'gain', 'muscle_gain')),
  gender text not null check (gender in ('male', 'female')),
  age int not null check (age between 10 and 100),
  height_cm numeric not null check (height_cm between 100 and 230),
  weight_kg numeric not null check (weight_kg between 30 and 200),
  activity text not null check (activity in ('sedentary', 'light', 'moderate', 'active', 'very_active')),
  allergies text[] not null default '{}',
  diet_type text not null check (diet_type in ('general', 'low_carb', 'vegan', 'intermittent_fasting')),
  has_condition boolean not null default false,
  condition_note text,
  cooking_time text not null check (cooking_time in ('low', 'medium', 'high')),

  -- 계산된 식단 결과 (web/src/lib/nutrition.ts와 동일한 로직 결과값)
  bmr int not null,
  tdee int not null,
  target_calories int not null,
  protein_g int not null,
  fat_g int not null,
  carb_g int not null
);

alter table public.onboarding_submissions enable row level security;

-- 누구나(비로그인 포함) 자기 응답을 저장할 수 있음 — 결과 조회/수정은 불가 (프론트에서 다시 못 읽음).
-- 실제 데이터 확인은 Supabase 대시보드(Table Editor) 또는 서버(Secret key)에서만.
create policy "onboarding_submissions: 누구나 저장 가능" on public.onboarding_submissions
  for insert
  to anon, authenticated
  with check (true);
