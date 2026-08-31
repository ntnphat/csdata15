-- =====================================================================
-- Đề án CS Data - Schema Supabase (PostgreSQL)
-- Chạy toàn bộ file này trong Supabase Dashboard > SQL Editor > New query
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. BẢNG DỮ LIỆU PHIM (đã làm sạch bởi pipeline ETL)
-- ---------------------------------------------------------------------
drop table if exists public.movies cascade;

create table public.movies (
    id                 bigserial primary key,
    name               text        not null,
    rating             text,
    rating_group       text,
    genre              text,
    year               integer,
    year_reported      integer,
    release_date       date,
    release_month      integer,
    season             text,
    decade             integer,
    score              numeric(3, 1),
    votes              numeric,
    director           text,
    writer             text,
    star               text,
    country            text,
    company            text,
    runtime            numeric,
    budget             numeric,      -- USD danh nghĩa theo năm phát hành
    gross              numeric,      -- USD danh nghĩa theo năm phát hành
    budget_real        numeric,      -- USD giá thực 2020 (đã khử lạm phát CPI-U)
    gross_real         numeric,
    profit_real        numeric,
    multiple           numeric,      -- gross_real / budget_real
    roi                numeric,      -- profit_real / budget_real
    has_financials     boolean default false,
    is_profitable_real boolean default false,
    budget_tier        text,
    created_at         timestamptz default now()
);

-- Index phục vụ các bộ lọc chính của dashboard
create index movies_year_idx        on public.movies (year);
create index movies_genre_idx       on public.movies (genre);
create index movies_rating_idx      on public.movies (rating_group);
create index movies_country_idx     on public.movies (country);
create index movies_financials_idx  on public.movies (has_financials);

alter table public.movies enable row level security;

-- Dữ liệu phim là dữ liệu tham chiếu: mọi người đọc được, chỉ service key ghi được.
create policy "movies_read_all"
    on public.movies for select
    to anon, authenticated
    using (true);


-- ---------------------------------------------------------------------
-- 2. HỒ SƠ NGƯỜI DÙNG
-- ---------------------------------------------------------------------
create table if not exists public.profiles (
    id         uuid primary key references auth.users (id) on delete cascade,
    email      text,
    full_name  text,
    created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "profiles_select_own"
    on public.profiles for select
    to authenticated
    using (auth.uid() = id);

create policy "profiles_upsert_own"
    on public.profiles for insert
    to authenticated
    with check (auth.uid() = id);

create policy "profiles_update_own"
    on public.profiles for update
    to authenticated
    using (auth.uid() = id);

-- Tự tạo hồ sơ ngay khi có tài khoản mới trong auth.users
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, email, full_name)
    values (new.id, new.email, coalesce(new.raw_user_meta_data ->> 'full_name', ''))
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();


-- ---------------------------------------------------------------------
-- 3. BỘ LỌC PHÂN TÍCH NGƯỜI DÙNG LƯU LẠI
-- ---------------------------------------------------------------------
create table if not exists public.saved_views (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references auth.users (id) on delete cascade,
    view_name  text not null,
    filters    jsonb not null default '{}'::jsonb,
    created_at timestamptz default now()
);

create index if not exists saved_views_user_idx on public.saved_views (user_id, created_at desc);

alter table public.saved_views enable row level security;

create policy "saved_views_own"
    on public.saved_views for all
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);


-- ---------------------------------------------------------------------
-- 4. NHẬT KÝ HỎI ĐÁP VỚI TRỢ LÝ AI
-- ---------------------------------------------------------------------
create table if not exists public.chat_logs (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references auth.users (id) on delete cascade,
    question   text not null,
    answer     text,
    created_at timestamptz default now()
);

create index if not exists chat_logs_user_idx on public.chat_logs (user_id, created_at desc);

alter table public.chat_logs enable row level security;

create policy "chat_logs_own"
    on public.chat_logs for all
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);


-- ---------------------------------------------------------------------
-- 5. VIEW TỔNG HỢP DÙNG CHO BI / KIỂM TRA NHANH
-- ---------------------------------------------------------------------
create or replace view public.v_genre_performance as
select
    genre,
    count(*)                                             as titles,
    percentile_cont(0.5) within group (order by budget_real) as median_budget,
    percentile_cont(0.5) within group (order by gross_real)  as median_gross,
    percentile_cont(0.5) within group (order by multiple)    as median_multiple,
    round(avg(case when is_profitable_real then 1 else 0 end) * 100, 2) as hit_rate
from public.movies
where has_financials
group by genre
order by median_multiple desc;
