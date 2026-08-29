-- auth.users.email은 text가 아니라 character varying이라, RETURNS TABLE(email text, ...)와
-- 타입이 안 맞아 "structure of query does not match function result type" 에러가 났다.
-- ::text로 명시적으로 캐스팅해서 해결한다.
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
      u.email::text,
      coalesce(u.raw_app_meta_data->>'provider', 'email') as provider,
      u.created_at
    from auth.users u
    order by u.created_at desc;
end;
$$;
