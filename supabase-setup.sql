-- Run this in the Supabase SQL editor: https://app.supabase.com → your project → SQL editor

-- Table: read_items — tracks which URLs a user has marked as read
create table if not exists read_items (
  id          bigserial primary key,
  user_id     uuid references auth.users(id) on delete cascade not null,
  url         text not null,
  read_at     timestamptz default now() not null,
  unique(user_id, url)
);
alter table read_items enable row level security;
create policy "Users manage their own read items"
  on read_items for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Table: news_roster — user's personal reading list (from "Add to my roster")
create table if not exists news_roster (
  id          bigserial primary key,
  user_id     uuid references auth.users(id) on delete cascade not null,
  person      text not null,
  role        text,
  platform    text,
  color       text,
  url         text,
  added_at    timestamptz default now() not null,
  unique(user_id, url)
);
alter table news_roster enable row level security;
create policy "Users manage their own roster"
  on news_roster for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Table: subscribers — email newsletter sign-ups (open insert, no auth required)
create table if not exists subscribers (
  id            bigserial primary key,
  email         text unique not null,
  subscribed_at timestamptz default now() not null
);
alter table subscribers enable row level security;
create policy "Anyone can subscribe"
  on subscribers for insert
  with check (true);
create policy "Service role reads subscribers"
  on subscribers for select
  using (auth.role() = 'service_role');

-- After running this SQL:
-- 1. Go to Authentication → Providers in your Supabase dashboard
-- 2. Enable Google: add Client ID + Secret from console.cloud.google.com
-- 3. Enable GitHub: add Client ID + Secret from github.com/settings/applications
-- 4. Set redirect URL in each OAuth app to: https://daily-product-news.vercel.app
-- 5. Paste your SUPABASE_URL and SUPABASE_ANON_KEY into index.html
