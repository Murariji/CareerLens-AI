-- CareerLens AI: anonymous usage stats + reliable keep-warm ping, for a free Supabase project.
--
-- Run once in Supabase → SQL Editor (or via a migration). Safe to re-run.
-- Stores no resume text and no personal data: only event type, time, a daily-rotating
-- visitor hash, a broad role category, the match score and whether AI was used.
--
-- After running it, set these on Render (CareerLens-AI → Environment):
--   CAREERLENS_SUPABASE_URL  = https://<project-ref>.supabase.co
--   CAREERLENS_SUPABASE_KEY  = the project's publishable (anon) key
--   CAREERLENS_STATS_TOKEN   = result of:  select value from careerlens.config where key = 'stats_token';

-- 1. Private schema: not exposed through the REST API.
create schema if not exists careerlens;
revoke all on schema careerlens from public, anon, authenticated;

create table if not exists careerlens.events (
  id            bigint generated always as identity primary key,
  created_at    timestamptz not null default now(),
  kind          text not null check (kind in ('visit', 'analysis')),
  visitor       text check (visitor is null or length(visitor) <= 64),
  role_category text check (role_category is null or length(role_category) <= 40),
  score         smallint check (score is null or score between 0 and 100),
  ai            boolean
);
create index if not exists events_kind_created_at_idx on careerlens.events (kind, created_at);
alter table careerlens.events enable row level security;

create table if not exists careerlens.config (
  key   text primary key,
  value text not null
);
alter table careerlens.config enable row level security;

-- Secret that only the CareerLens backend knows; required to write events.
insert into careerlens.config (key, value)
values ('stats_token', replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''))
on conflict (key) do nothing;

-- 2. Write function: callable with the publishable key, but rejects calls without the token.
create or replace function public.careerlens_record_event(
  p_token text,
  p_kind text,
  p_visitor text default null,
  p_role_category text default null,
  p_score integer default null,
  p_ai boolean default null
) returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if p_token is distinct from (select value from careerlens.config where key = 'stats_token') then
    raise exception 'invalid stats token' using errcode = '42501';
  end if;
  insert into careerlens.events (kind, visitor, role_category, score, ai)
  values (p_kind, p_visitor, p_role_category, p_score, p_ai);
end;
$$;

revoke all on function public.careerlens_record_event(text, text, text, text, integer, boolean) from public;
grant execute on function public.careerlens_record_event(text, text, text, text, integer, boolean) to anon, authenticated;

-- 3. Read function: aggregate totals only (no individual events).
create or replace function public.careerlens_stats()
returns json
language sql
stable
security definer
set search_path = ''
as $$
  select json_build_object(
    'visits',          (select count(*) from careerlens.events where kind = 'visit'),
    'unique_visitors', (select count(distinct (created_at::date)::text || ':' || visitor)
                          from careerlens.events where kind = 'visit' and visitor is not null),
    'analyses',        (select count(*) from careerlens.events where kind = 'analysis'),
    'ai_analyses',     (select count(*) from careerlens.events where kind = 'analysis' and ai),
    'average_score',   (select round(avg(score)) from careerlens.events where kind = 'analysis'),
    'roles',           coalesce((
                          select json_object_agg(category, total order by total desc)
                          from (
                            select coalesce(role_category, 'Other') as category, count(*) as total
                            from careerlens.events where kind = 'analysis' group by 1
                          ) as by_role
                        ), '{}'::json),
    'last_30_days',    (
                          select json_agg(json_build_object(
                                   'day', day::date,
                                   'visits', (select count(*) from careerlens.events e
                                              where e.kind = 'visit' and e.created_at::date = day::date),
                                   'analyses', (select count(*) from careerlens.events e
                                                where e.kind = 'analysis' and e.created_at::date = day::date)
                                 ) order by day)
                          from generate_series(current_date - 29, current_date, interval '1 day') as day
                        )
  );
$$;

revoke all on function public.careerlens_stats() from public;
grant execute on function public.careerlens_stats() to anon, authenticated;

-- 4. Reliable keep-warm: Supabase's own cron pings the Render backend every 5 minutes,
--    so the free server never falls asleep between visitors.
create extension if not exists pg_net;
create extension if not exists pg_cron;

select cron.schedule(
  'careerlens-keep-warm',
  '*/5 * * * *',
  $$ select net.http_get('https://careerlens-ai-z6xa.onrender.com/api/health') $$
);
