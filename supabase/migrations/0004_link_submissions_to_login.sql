-- 로그인(Google/Kakao) 도입: onboarding_submissions를 auth.users와 연결한다.
-- 로그인 없이 저장한 기록(user_id null)도 계속 지원하므로 컬럼은 nullable.
alter table onboarding_submissions
  add column if not exists user_id uuid references auth.users(id) on delete set null;

-- 본인 소유 행만 직접 조회 가능하게 허용(다른 테이블 전체 스캔은 여전히 불가 —
-- 이 정책은 auth.uid() = user_id인 행에만 매칭되므로 로그인 안 한 요청은 아무것도 못 봄).
create policy "본인 기록만 조회 가능"
  on onboarding_submissions for select
  to authenticated
  using (auth.uid() = user_id);
