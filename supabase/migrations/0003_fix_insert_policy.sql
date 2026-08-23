-- 처음엔 "결과 저장하기"가 42501(row-level security policy violation)로 실패해서 INSERT
-- 정책이 빠졌나 의심하고 이 마이그레이션을 만들었다. 실제로 실행해서 pg_policies로 확인해보니
-- 정책은 이미 정상이었음 — 진짜 원인은 다른 곳(웹 코드가 insert에 .select()를 붙여서, 없는
-- SELECT 권한을 요구하고 있었음, web/src/components/onboarding/onboarding-quiz.tsx에서 수정)
-- 이었다. 이 파일은 실질적으로 no-op이지만(drop 후 같은 정책 재생성), 실행해서 해가 될 건
-- 없고 정책 상태를 눈으로 확인하는 용도로는 유효해서 남겨둔다.
-- Supabase SQL Editor에 붙여넣어 실행합니다.

drop policy if exists "onboarding_submissions: 누구나 저장 가능" on public.onboarding_submissions;

create policy "onboarding_submissions: 누구나 저장 가능" on public.onboarding_submissions
  for insert
  to anon, authenticated
  with check (true);

-- 확인용: 실행 후 결과 창에 이 정책이 실제로 떠야 정상 적용된 것.
-- roles 컬럼에 {anon,authenticated}가 보여야 함.
select policyname, cmd, roles, with_check
from pg_policies
where tablename = 'onboarding_submissions';
