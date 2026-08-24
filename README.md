# 模板库

网页端可复用打印模板库：上传 Word 一键建模板，可变字段（文本/数字/日期/表格）填入即可打印输出。配套 Supabase 后端可实现全班免登录共享模板。

## 直接使用

本地或部署到 GitHub Pages 后，浏览器打开 `index.html` 即可使用。无需构建步骤。

- **建模板**：顶栏「📄 导入 Word 建模板」，在 Word 里用 `{{字段名}}` 标记需要替换的位置即可上传
- **填字段**：含「名单/明细/表」字样的占位符会自动识别为表格字段，可上传 Excel 或粘贴数据
- **打印**：右侧实时预览 →「🖨️ 打印 / 导出 PDF」

## 启用云同步（可选，Supabase）

1. 注册 Supabase → New project
2. 在 SQL Editor 跑 `supabase/schema.sql`（建表 + RLS）
3. 在 `js/config.js` 填入 `SUPABASE_URL` 与 `SUPABASE_ANON_KEY`

未配置时自动降级为本地（localStorage）模式，功能不受影响。

## 文件结构

- `index.html` + `css/` + `js/` — 前端应用
- `lib/` — 内置离线依赖：mammoth (Word→HTML)、xlsx (Excel 读取)、supabase-js (云端 SDK)
- `supabase/schema.sql` — 云端建表脚本
- `samples/` — 模板生成与端到端验证脚本（可不部署）

## 注意

anon key 暴露在前端 → 任何访问者都可改模板（适用于班级内部非敏感共享）。如需权限控制，请在 `supabase/schema.sql` 中启用 RLS 鉴权策略。
