-- 온보딩 결과에 AI가 생성한 식단(meal_plan)도 함께 저장하고,
-- "결과 저장하기" 후 받는 링크(/plan/[id])로 언제든 다시 볼 수 있게 한다.
-- Supabase SQL Editor에 붙여넣어 실행합니다.

-- 1) AI 추천 식단(JSON)을 저장할 컬럼 추가.
alter table public.onboarding_submissions
  add column if not exists meal_plan jsonb;

-- 2) 공유 가능한 결과 링크용 조회 함수.
--    onboarding_submissions 테이블 자체에는 select 정책을 열지 않는다 — `using (true)`로 열면
--    익명 키로 테이블 전체를 스캔할 수 있어(email 등 민감정보 포함) 위험하다.
--    대신 SECURITY DEFINER 함수로 "id 하나를 정확히 아는 사람"만 그 한 행을 조회할 수 있게 하고,
--    email/condition_note(기저질환 메모)처럼 더 민감한 항목은 반환 목록에서 아예 뺀다.
create or replace function public.get_submission_report(p_id uuid)
returns table (
  id uuid,
  created_at timestamptz,
  goal text,
  gender text,
  diet_type text,
  activity text,
  allergies text[],
  cooking_time text,
  has_condition boolean,
  bmr int,
  tdee int,
  target_calories int,
  protein_g int,
  fat_g int,
  carb_g int,
  meal_plan jsonb
)
language sql
security definer
set search_path = public
as $$
  select id, created_at, goal, gender, diet_type, activity, allergies, cooking_time,
         has_condition, bmr, tdee, target_calories, protein_g, fat_g, carb_g, meal_plan
  from public.onboarding_submissions
  where id = p_id;
$$;

grant execute on function public.get_submission_report(uuid) to anon, authenticated;
