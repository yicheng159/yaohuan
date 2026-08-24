-- ============================================================
-- 打印模板库 · 云端同步表（Supabase / Postgres）
-- 用途：全班免登录共享同一套模板（公共表，任何人可读写）
-- 执行方式：Supabase 控制台 → SQL Editor → 粘贴本文件 → Run
-- ============================================================

-- 1) 模板表
create table if not exists public.templates (
  id          text primary key,                       -- 模板唯一 id（前端生成）
  name        text not null,                          -- 模板名称
  description text default '',                        -- 说明
  settings    jsonb not null default '{}'::jsonb,     -- 纸张/字体/边距等设置
  fields      jsonb not null default '[]'::jsonb,     -- 字段结构数组
  content     text default '',                        -- 正文 HTML（含 {{占位符}}）
  updated_at  bigint not null default 0,              -- 最后更新时间戳(ms)
  created_at  bigint not null default 0               -- 创建时间戳(ms)
);

-- 2) 开启行级安全（RLS），再显式允许 anon 角色全表读写
alter table public.templates enable row level security;

-- 免登录共享：允许匿名(annon/anon)角色对整个表 select/insert/update/delete
-- 注意：anon key 会暴露在前端，因此本方案下任何人都能改模板——班级内部共享足够。
drop policy if exists "templates_anon_all" on public.templates;
create policy "templates_anon_all"
  on public.templates
  for all
  to anon
  using ( true )
  with check ( true );

-- 若你启用了登录(auth)，可额外保留 authenticated 权限（本方案未用）：
drop policy if exists "templates_auth_all" on public.templates;
create policy "templates_auth_all"
  on public.templates
  for all
  to authenticated
  using ( true )
  with check ( true );

-- 3) 便于按更新时间排序的索引
create index if not exists templates_updated_at_idx
  on public.templates (updated_at desc);

-- 完成提示
-- 之后到 Project Settings → API 复制：Project URL 与 anon public key，
-- 填入应用 js/config.js 的 SUPABASE_URL / SUPABASE_ANON_KEY 即可启用云同步。
