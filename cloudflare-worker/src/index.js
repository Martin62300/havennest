function jsonResponse(data, status = 200, headers = {}) {
  const h = new Headers(headers)
  if (!h.has("content-type")) h.set("content-type", "application/json; charset=utf-8")
  return new Response(JSON.stringify(data), { status, headers: h })
}

function withCors(resp, origin) {
  const h = new Headers(resp.headers)
  h.set("access-control-allow-origin", origin || "*")
  h.set("access-control-allow-methods", "GET,POST,PATCH,DELETE,OPTIONS")
  h.set("access-control-allow-headers", "content-type,x-webhook-secret")
  h.set("access-control-max-age", "86400")
  return new Response(resp.body, { status: resp.status, headers: h })
}

function base64Url(bytes) {
  let s = ""
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "")
}

async function sha256Hex(input) {
  const data = new TextEncoder().encode(input)
  const buf = await crypto.subtle.digest("SHA-256", data)
  const arr = new Uint8Array(buf)
  return Array.from(arr).map(b => b.toString(16).padStart(2, "0")).join("")
}

function getEnvString(env, key, fallback = "") {
  const v = (env[key] || "").toString().trim()
  return v || fallback
}

async function airtableRequest(env, path, init = {}) {
  const baseId = getEnvString(env, "AIRTABLE_BASE_ID")
  const token = getEnvString(env, "AIRTABLE_TOKEN")
  if (!baseId || !token) {
    throw new Error("Airtable env not configured")
  }
  const url = `https://api.airtable.com/v0/${encodeURIComponent(baseId)}${path}`
  const headers = new Headers(init.headers || {})
  headers.set("authorization", `Bearer ${token}`)
  if (init.body && !headers.has("content-type")) headers.set("content-type", "application/json")
  const res = await fetch(url, { ...init, headers })
  const text = await res.text()
  let data
  try { data = text ? JSON.parse(text) : null } catch { data = { raw: text } }
  if (!res.ok) {
    const msg = typeof data === "object" && data && data.error && data.error.message ? data.error.message : `Airtable error ${res.status}`
    const e = new Error(msg)
    e.status = res.status
    e.data = data
    throw e
  }
  return data
}

async function resendEmail(env, to, subject, html) {
  const apiKey = getEnvString(env, "RESEND_API_KEY")
  const from = getEnvString(env, "RESEND_FROM")
  if (!apiKey || !from) {
    throw new Error("Resend env not configured")
  }
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "authorization": `Bearer ${apiKey}`,
      "content-type": "application/json"
    },
    body: JSON.stringify({ from, to, subject, html })
  })
  const text = await res.text()
  if (!res.ok) {
    throw new Error(`Resend error ${res.status}: ${text}`)
  }
  return text ? JSON.parse(text) : {}
}

function getStatusField(fields) {
  return fields["Status"] ?? fields["status"] ?? fields["状态 (Status)"] ?? ""
}

function normalizeStatus(v) {
  return (v || "").toString().trim().toLowerCase()
}

function firstExistingKey(fields, keys, fallback = "") {
  for (const k of keys) {
    if (Object.prototype.hasOwnProperty.call(fields, k)) return k
  }
  return fallback || keys[0] || ""
}

function firstFieldValue(fields, keys, fallback = "") {
  for (const k of keys) {
    const v = fields[k]
    if (v !== undefined && v !== null && String(v).trim() !== "") return v
  }
  return fallback
}

function parseFirstInt(v) {
  if (typeof v === "number" && Number.isFinite(v)) return Math.trunc(v)
  const s = (v ?? "").toString()
  const m = s.match(/(\d+)/)
  if (!m) return NaN
  const n = Number(m[1])
  return Number.isFinite(n) ? Math.trunc(n) : NaN
}

function allowedUpdateFields(body, existingFields) {
  const out = {}
  if (typeof body.title === "string") out["房源标题 (Listing Title)"] = body.title.trim()
  if (typeof body.price === "number") out["月租金 (Monthly Rent)"] = body.price
  if (typeof body.price === "string" && body.price.trim()) {
    const n = Number(body.price.trim().replace(/[^0-9.]/g, ""))
    if (!Number.isNaN(n)) out["月租金 (Monthly Rent)"] = Math.floor(n)
  }
  if (typeof body.address === "string") out["房源具体地址 (Address)"] = body.address.trim()
  if (typeof body.city === "string") {
    out["所属城市 (City)"] = body.city.trim()
  }
  if (typeof body.beds !== "undefined") {
    // 直接传递字符串或数字，Airtable 的字段如果是 Single Select 会要求严格匹配选项字符串
    out["卧室数量 (Beds)"] = String(body.beds).trim()
  }
  if (typeof body.desc === "string") out["房源描述 (Description)"] = body.desc
  return out
}

async function findRecordByTokenHash(env, tokenHash) {
  const table = getEnvString(env, "AIRTABLE_TABLE_NAME", "Table 1")
  const formula = `{manage_token_hash}='${tokenHash}'`
  const params = new URLSearchParams({ filterByFormula: formula, maxRecords: "1" })
  const data = await airtableRequest(env, `/${encodeURIComponent(table)}?${params.toString()}`, { method: "GET" })
  const rec = (data.records || [])[0]
  return rec || null
}

async function hookNewListing(env, req) {
  const secret = getEnvString(env, "WEBHOOK_SECRET")
  const got = req.headers.get("x-webhook-secret") || ""
  if (!secret || got !== secret) {
    return jsonResponse({ ok: false, error: "unauthorized" }, 401)
  }

  const body = await req.json().catch(() => null)
  const recordId = body && typeof body.recordId === "string" ? body.recordId.trim() : ""
  if (!recordId) return jsonResponse({ ok: false, error: "recordId required" }, 400)

  const table = getEnvString(env, "AIRTABLE_TABLE_NAME", "Table 1")
  const rec = await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(recordId)}`, { method: "GET" })
  const fields = rec.fields || {}
  const email = (fields["电子邮箱 (Email)"] || fields["Email"] || fields["email"] || "").toString().trim()
  if (!email) return jsonResponse({ ok: false, error: "email missing in record" }, 400)

  const statusNow = normalizeStatus(getStatusField(fields))
  if (statusNow && ["deleted", "inactive", "off", "disabled"].includes(statusNow)) {
    return jsonResponse({ ok: true, skipped: true, reason: "inactive_or_deleted" }, 200)
  }

  const tokenBytes = crypto.getRandomValues(new Uint8Array(24))
  const token = base64Url(tokenBytes)
  const tokenHash = await sha256Hex(token)
  const nowIso = new Date().toISOString()
  const nowDate = nowIso.slice(0, 10)

  const updateFields = {
    "manage_token_hash": tokenHash,
    "manage_token_created_at": nowDate,
    "manage_email_sent_at": nowDate
  }
  if (!getStatusField(fields)) updateFields["Status"] = "active"

  try {
    await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(recordId)}`, {
      method: "PATCH",
      body: JSON.stringify({ fields: updateFields })
    })
  } catch (e) {
    try {
      const retryFields = { ...updateFields, "manage_token_created_at": nowIso, "manage_email_sent_at": nowIso }
      await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(recordId)}`, {
        method: "PATCH",
        body: JSON.stringify({ fields: retryFields })
      })
    } catch (e2) {
      const minimalFields = { "manage_token_hash": tokenHash }
      if (!getStatusField(fields)) minimalFields["Status"] = "active"
      await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(recordId)}`, {
        method: "PATCH",
        body: JSON.stringify({ fields: minimalFields })
      })
    }
  }

  const siteOrigin = getEnvString(env, "SITE_ORIGIN", "https://havennestapp.com").replace(/\/+$/g, "")
  const apiOrigin = new URL(req.url).origin
  const manageUrl = `${siteOrigin}/manage.html?token=${encodeURIComponent(token)}&api=${encodeURIComponent(apiOrigin)}`

  const title = (fields["房源标题 (Listing Title)"] || "你的房源").toString()
  const subject = "HavenNest 房源管理链接"
  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; line-height:1.6; color:#0b1b33;">
      <h2 style="margin:0 0 10px;">你的房源已发布</h2>
      <div style="margin:0 0 14px; color:#334155;">${title}</div>
      <div style="margin:16px 0 12px; color:#475569;">点击下面按钮管理你的房源（修改/下架/删除）：</div>
      <div style="margin:0 0 16px;">
        <a href="${manageUrl}" style="display:inline-block; background:#002147; color:#ffffff; text-decoration:none; padding:12px 16px; border-radius:12px; font-weight:800;">
          打开房源管理页面
        </a>
      </div>
      <div style="color:#64748b; font-size:12px;">如果按钮无法打开，可复制此链接到浏览器：<br><span style="word-break:break-all;">${manageUrl}</span></div>
    </div>
  `

  await resendEmail(env, email, subject, html)

  return jsonResponse({ ok: true, recordId, emailed: true })
}

async function apiManage(env, req, url) {
  const token = (url.searchParams.get("token") || "").trim()
  if (!token) return jsonResponse({ ok: false, error: "token required" }, 400)
  const tokenHash = await sha256Hex(token)
  const rec = await findRecordByTokenHash(env, tokenHash)
  if (!rec) return jsonResponse({ ok: false, error: "not_found" }, 404)

  const fields = rec.fields || {}
  const status = normalizeStatus(getStatusField(fields))
  if (status && ["deleted"].includes(status)) return jsonResponse({ ok: false, error: "not_found" }, 404)

  const table = getEnvString(env, "AIRTABLE_TABLE_NAME", "Table 1")

  if (req.method === "GET") {
    return jsonResponse({
      ok: true,
      recordId: rec.id,
      listing: {
        title: fields["房源标题 (Listing Title)"] || "",
        price: fields["月租金 (Monthly Rent)"] || 0,
        address: fields["房源具体地址 (Address)"] || "",
        city: firstFieldValue(fields, ["所属城市 (City)", "所在城市 (City)"], ""),
        beds: fields["卧室数量 (Beds)"] || "",
        desc: fields["房源描述 (Description)"] || "",
        status: status || "active"
      }
    })
  }

  if (req.method === "PATCH") {
    const body = await req.json().catch(() => ({}))
    const updates = allowedUpdateFields(body, fields)
    if (Object.keys(updates).length === 0) return jsonResponse({ ok: false, error: "no_valid_fields" }, 400)
    await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(rec.id)}`, {
      method: "PATCH",
      body: JSON.stringify({ fields: updates })
    })
    return jsonResponse({ ok: true })
  }

  if (req.method === "POST") {
    const action = (url.searchParams.get("action") || "").trim().toLowerCase()
    if (!action) return jsonResponse({ ok: false, error: "action required" }, 400)
    if (action === "offline") {
      await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(rec.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ fields: { "Status": "inactive" } })
      })
      return jsonResponse({ ok: true })
    }
    if (action === "online") {
      await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(rec.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ fields: { "Status": "active" } })
      })
      return jsonResponse({ ok: true })
    }
    if (action === "delete") {
      const nowDate = new Date().toISOString().slice(0, 10)
      try {
        await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(rec.id)}`, {
          method: "PATCH",
          body: JSON.stringify({ fields: { "Status": "deleted", "manage_deleted_at": nowDate } })
        })
      } catch (e) {
        await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(rec.id)}`, {
          method: "PATCH",
          body: JSON.stringify({ fields: { "Status": "deleted" } })
        })
      }
      return jsonResponse({ ok: true })
    }
    return jsonResponse({ ok: false, error: "unknown_action" }, 400)
  }

  return jsonResponse({ ok: false, error: "method_not_allowed" }, 405)
}

function normalizeOwnerListingFromFields(recordId, fields) {
  const title = (fields["房源标题 (Listing Title)"] || "Rental Listing").toString()
  const addr = (fields["房源具体地址 (Address)"] || "Vancouver").toString()
  const status = normalizeStatus(getStatusField(fields)) || "active"
  
  let city = firstFieldValue(fields, ["所属城市 (City)", "所在城市 (City)"], "").toString()
  if (!city) {
    const searchStr = (title + " " + addr).toLowerCase()
    if (searchStr.includes("richmond") || searchStr.includes("列治文") || searchStr.includes("lansdowne")) {
      city = "Richmond"
    } else if (searchStr.includes("burnaby") || searchStr.includes("本拿比")) {
      city = "Burnaby"
    } else {
      city = "Vancouver"
    }
  }

  const bedsRaw = fields["卧室数量 (Beds)"]
  let bedsNum = parseFirstInt(bedsRaw)
  if (Number.isNaN(bedsNum)) {
    const descStr = (fields["房源描述 (Description)"] || "").toString().toLowerCase()
    const searchStr = (title + " " + descStr).toLowerCase()
    const match = searchStr.match(/(\d+)\s*(?:室|房|br|bed|bedroom)/)
    if (match) {
      bedsNum = Number(match[1])
    } else if (searchStr.includes("studio") || searchStr.includes("bachelor")) {
      bedsNum = 0
    } else {
      bedsNum = 1
    }
  }

  const priceRaw = fields["月租金 (Monthly Rent)"]
  const priceNum = typeof priceRaw === "number" ? priceRaw : Number(String(priceRaw || "").replace(/[^0-9.]/g, ""))

  const rawPhotos = Array.isArray(fields["房源照片 / Property Photos"]) ? fields["房源照片 / Property Photos"] : []
  const photos = rawPhotos.map(x => (x && x.url ? String(x.url) : "")).filter(Boolean)

  return {
    id: recordId,
    source: "owner",
    title,
    price: Number.isFinite(priceNum) ? Math.floor(priceNum) : 0,
    url: `https://havennestapp.com/listing/${recordId}`,
    address: addr,
    city,
    beds: Number.isFinite(bedsNum) ? bedsNum : 0,
    lat: null,
    lng: null,
    image: photos[0] || "",
    images: photos,
    desc: (fields["房源描述 (Description)"] || "").toString(),
    phone: (fields["联系电话 (Phone)"] || "").toString(),
    email: (fields["电子邮箱 (Email)"] || "").toString(),
    isPromo: true,
    date: new Date().toISOString().slice(0, 10),
    status
  }
}

async function apiPublicListings(env) {
  const table = getEnvString(env, "AIRTABLE_TABLE_NAME", "Table 1")
  const out = []
  let offset = ""
  let guard = 0

  while (guard < 10) {
    guard += 1
    const params = new URLSearchParams({ pageSize: "100" })
    if (offset) params.set("offset", offset)
    const data = await airtableRequest(env, `/${encodeURIComponent(table)}?${params.toString()}`, { method: "GET" })
    const records = Array.isArray(data.records) ? data.records : []
    for (const r of records) {
      const fields = r && r.fields ? r.fields : {}
      const status = normalizeStatus(getStatusField(fields))
      if (status && ["inactive", "deleted", "off", "disabled"].includes(status)) continue
      out.push(normalizeOwnerListingFromFields(r.id, fields))
    }
    offset = typeof data.offset === "string" ? data.offset : ""
    if (!offset) break
  }

  return jsonResponse(
    { ok: true, listings: out },
    200,
    { "cache-control": "public, max-age=60" }
  )
}

async function purgeDeletedRecords(env) {
  const table = getEnvString(env, "AIRTABLE_TABLE_NAME", "Table 1")
  const daysRaw = getEnvString(env, "PURGE_DELETED_AFTER_DAYS", "0")
  const days = Math.max(0, Number(daysRaw) || 0)
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000

  let offset = ""
  let guard = 0

  while (guard < 10) {
    guard += 1
    const params = new URLSearchParams({
      pageSize: "100",
      filterByFormula: "LOWER({Status})='deleted'"
    })
    if (offset) params.set("offset", offset)
    const data = await airtableRequest(env, `/${encodeURIComponent(table)}?${params.toString()}`, { method: "GET" })
    const records = Array.isArray(data.records) ? data.records : []
    for (const r of records) {
      const f = r && r.fields ? r.fields : {}
      const deletedAt = f && f["manage_deleted_at"] ? Date.parse(String(f["manage_deleted_at"])) : NaN
      const createdTime = r && r.createdTime ? Date.parse(r.createdTime) : NaN
      const t = Number.isFinite(deletedAt) ? deletedAt : createdTime
      if (Number.isFinite(t) && t > cutoff) continue
      await airtableRequest(env, `/${encodeURIComponent(table)}/${encodeURIComponent(r.id)}`, { method: "DELETE" })
    }
    offset = typeof data.offset === "string" ? data.offset : ""
    if (!offset) break
  }
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url)
    const origin = getEnvString(env, "CORS_ORIGIN", getEnvString(env, "SITE_ORIGIN", "*"))
    if (req.method === "OPTIONS") return withCors(new Response(null, { status: 204 }), origin)

    try {
      if (url.pathname === "/api/hooks/airtable/new-listing" && req.method === "POST") {
        return withCors(await hookNewListing(env, req), origin)
      }
      if (url.pathname === "/api/manage") {
        return withCors(await apiManage(env, req, url), origin)
      }
      if (url.pathname === "/api/public/listings" && req.method === "GET") {
        return withCors(await apiPublicListings(env), origin)
      }
      return withCors(jsonResponse({ ok: false, error: "not_found" }, 404), origin)
    } catch (e) {
      return withCors(jsonResponse({ ok: false, error: e && e.message ? e.message : "error" }, 500), origin)
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(purgeDeletedRecords(env))
  }
}
