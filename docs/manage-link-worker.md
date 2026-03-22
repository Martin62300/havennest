# 0 阶段：免登录发布 + 邮件发送管理链接（Cloudflare Worker）

## 目标
- 屋主无需注册即可发布房源
- 系统自动发送“管理链接”到屋主邮箱
- 屋主可用链接自助修改 / 下架 / 删除房源
- 前端保持静态站（GitHub Pages），敏感密钥只存在 Worker 环境变量中

## 一、Airtable 需要新增字段
在你的房源表（默认 Table 1）新增以下字段（字段名需严格一致）：
- `manage_token_hash`（Single line text）
- `manage_token_created_at`（Date）
- `manage_email_sent_at`（Date）
- `Status`（Single select，建议选项：`active`、`inactive`、`deleted`）

并确保屋主邮箱字段存在（当前爬虫使用字段：`电子邮箱 (Email)`）。

## 二、部署 Cloudflare Worker
代码在仓库目录：
- `cloudflare-worker/src/index.js`

### 1) 创建 Worker
- Cloudflare Dashboard → Workers & Pages → Create → Worker
- 把 `cloudflare-worker/src/index.js` 内容粘贴进去并保存部署

### 2) 配置 Worker 环境变量（Settings → Variables）
需要添加（均为 Secret）：
- `AIRTABLE_TOKEN`：Airtable Personal Access Token（PAT）
- `AIRTABLE_BASE_ID`：你的 Base ID（形如 `appxxxxxxxxxxxxxx`）
- `AIRTABLE_TABLE_NAME`：表名（例如 `Table 1`）
- `WEBHOOK_SECRET`：你自定义的随机字符串（给 Airtable Automation 调用用）
- `RESEND_API_KEY`：Resend API Key
- `RESEND_FROM`：发件人（例如 `HavenNest <noreply@havennestapp.com>`）
- `SITE_ORIGIN`：网站域名（例如 `https://havennestapp.com`）
- `CORS_ORIGIN`：允许访问 API 的来源（建议同 `SITE_ORIGIN`）

## 三、把 Worker 挂到域名路由
建议把 Worker 路由到同域名的 `/api/*`，这样前端可直接请求相对路径：
- Workers & Pages → Worker → Triggers → Routes
- 添加 Route：`havennestapp.com/api/*`（按你的实际域名改）

## 四、Resend 配置
- Resend 控制台添加并验证你的域名
- 创建 API Key，填入 `RESEND_API_KEY`
- `RESEND_FROM` 必须是你在 Resend 里验证过的域名发件人

## 五、Airtable Automation：新房源触发发邮件
在 Airtable Automations 新建流程：
- Trigger：When record created（或 When record matches conditions）
- Action：Run a script

脚本示例（把 URL/secret 改成你自己的）：

```js
let inputConfig = input.config()
let recordId = inputConfig.recordId

let res = await fetch('https://havennestapp.com/api/hooks/airtable/new-listing', {
  method: 'POST',
  headers: {
    'content-type': 'application/json',
    'x-webhook-secret': '你的 WEBHOOK_SECRET'
  },
  body: JSON.stringify({ recordId })
})

let text = await res.text()
output.text(text)
```

并在脚本的 “Input variables” 添加：
- `recordId` → 绑定 Trigger 输出的 Record ID

## 六、管理页面
仓库已包含：
- `manage.html`
- `manage.js`

屋主收到邮件后打开：
- `https://havennestapp.com/manage.html?token=...`

功能：
- 修改标题/价格/地址/城市/卧室数/描述
- 下架/上架/删除（删除为状态标记 `deleted`）

## 七、爬虫端过滤下架/删除房源
爬虫已支持跳过：
- `Status` 为 `inactive/deleted/off/disabled`

对应代码在：
- `crawler.py` 的 `process_airtable_listings`
