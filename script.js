let allListings = [];
let filteredListings = [];
let curLang = 'zh';
let curSlide = 0;
let activeSvc = '';
let viewMode = 'card';
let pendingListingKey = '';
let currentListingKey = '';
let map = L.map('map', { scrollWheelZoom: false }).setView([49.24, -123.05], 11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const dict = {
    zh: {
        seoTitle: "HavenNest 安家居 | 大温全量房源聚合 & 一站式租房服务门户",
        seoDescription: "HavenNest 聚合大温各大平台房源，为您提供省时省心的全方位租房支持。从专业持牌团队提供的一站式租客保险咨询，到搬家、清洁对接，全程为您把控细节，让您的温哥华迁居之旅省心无忧。",
        postCta: "拥有空置房源？免费发布至平台",
        postBtn: "屋主发布",
        singleKeyBtn: "SingleKey 背调",
        next: "明白，下一步",
        agree: "同意授权并继续",
        gen: "生成正式申请表",
        copy: "复制文本",
        email: "打开邮件发送",
        name: "您的姓名",
        phone: "联系电话",
        emailLbl: "电子邮箱",
        dob: "出生日期（YYYY-MM-DD）",
        eff: "保单生效日期（YYYY-MM-DD）",
        addr: "房源具体地址",
        m_t2: "授权告知",
        m_c2: "作为大温专业持牌专家团队，我们承诺保护您的隐私。本人授权 HavenNest 将提供的信息安全地转交给我们的合作经纪进行报价。您的隐私受 BC 法律保护。",
        m_t3: "申请信息填写",
        m_t4: "表单生成成功",
        ins: "租客保险咨询",
        move: "专业搬家服务",
        clean: "退房清洁服务",
        footer: `<div style="max-width:1100px; margin:0 auto; line-height:1.7;">
                    <strong>免责声明：</strong>本站房源信息包含系统抓取与屋主直发，仅供参考，不构成任何要约或承诺。房源价格、空置情况、面积与配套等可能随时变更，请以原网站/发布者信息为准。<br>
                    <strong>第三方来源：</strong>系统抓取房源来自第三方公开页面（如 VanPeople、Rentals.ca、Craigslist 等），版权与内容权利归原网站及发布者所有。本站与上述第三方平台无隶属或合作关系。<br>
                    <strong>跳转与联系：</strong>系统抓取房源在本站仅展示摘要信息；联系与看房请点击“查看原房源”跳转回原网站完成。除屋主直发房源外，本站不会展示或主动收集/存储屋主、经纪人等个人联系方式。<br>
                    <strong>风险提示：</strong>请谨防诈骗，勿提前转账或提供敏感信息。本站对第三方链接内容与交易行为不承担责任。&copy; 2026 HavenNest App.
                 </div>`,
        insPop: `<h3>为何必须购买租客保险？</h3>
                <p style="color:#166534; font-weight:bold;">购买租客保险不仅是房东的普遍要求，更是为您自己的生活和财产安全焊死最后一道防线。</p>
                <ul style="text-align:left; line-height:1.8;">
                    <li><strong>财物保障：</strong>全面覆盖家具、电子产品及衣物。若因水灾、火灾或盗窃导致损失，保险将按重置价值赔付。</li>
                    <li><strong>责任赔付：</strong>承担因过失导致的法律赔偿（如忘关水龙头淹了楼下，或火锅起火），为您挡掉天价账单。</li>
                    <li><strong>访客保障：</strong>保障访客在您的租赁空间内意外受伤而产生的医疗或法律费用。</li>
                    <li><strong>额外生活费：</strong>若房屋因理赔维修无法居住，保险将支付您的酒店住宿及额外食宿补助。</li>
                </ul>`,
        city: "城市",
        beds: "卧室数量",
        budget: "预算",
        sort: "排序",
        view: "显示方式",
        viewCard: "大图模式",
        viewCompact: "小图模式",
        allCities: "全部城市",
        anyBeds: "不限卧室",
        noLimitBudget: "不限预算",
        all: "全部",
        any: "不限",
        lowHigh: "价格从低到高",
        highLow: "价格从高到低",
        bedsLowHigh: "房间数量从少到多",
        bedsHighLow: "房间数量从多到少",
        dateNewOld: "发布时间从新到旧",
        default: "默认",
        sourceCrawler: "系统抓取",
        sourceOwner: "屋主直发",
        viewDetail: "查看详情",
        contact: "联系方式",
        mapNotice: "📍 温馨提示：部分抓取房源因原网站地址信息不全，地图定位可能存在偏差，请以详情页描述为准。",
        filterHint: "💡 提示：此处的筛选条件会同步过滤上方地图中的房源"
    },
    en: {
        seoTitle: "Havennest | Greater Vancouver Aggregated Rental Listings & One-Stop Services",
        seoDescription: "Havennest aggregates rental listings across Greater Vancouver to provide a seamless, time-saving experience. From professional licensed tenant insurance support to moving and cleaning services, we handle the details so you can enjoy a worry-free move.",
        postCta: "Have a vacancy? Post it on HavenNest for free!",
        postBtn: "Post Now",
        singleKeyBtn: "SingleKey Screening",
        next: "Next Step",
        agree: "Agree & Authorize",
        gen: "Generate Application",
        copy: "Copy Text",
        email: "Send via Email",
        name: "Full Name",
        phone: "Phone Number",
        emailLbl: "Email Address",
        dob: "Date of Birth (YYYY-MM-DD)",
        eff: "Effective Date (YYYY-MM-DD)",
        addr: "Rental Address",
        m_t2: "Authorization",
        m_c2: "As a licensed professional team, we promise to protect your privacy. You authorize HavenNest to securely transfer your details to our partner broker for a quote. Your data is protected under BC law.",
        m_t3: "Application Details",
        m_t4: "Form Generated",
        ins: "Tenant Insurance",
        move: "Moving Service",
        clean: "Cleaning Service",
        footer: `<div style="max-width:1100px; margin:0 auto; line-height:1.7;">
                    <strong>Disclaimer:</strong> Listings on this site include both crawled content and direct owner posts and are provided for informational purposes only. Prices, availability, and details may change at any time; please verify on the original source or with the poster. <br>
                    <strong>Third‑Party Sources:</strong> Crawled listings are sourced from public third‑party pages (e.g., VanPeople, Rentals.ca, Craigslist). All rights remain with the original websites and posters. HavenNest is not affiliated with these third‑party platforms. <br>
                    <strong>Redirect & Contact:</strong> For crawled listings, this site shows summary information only. To contact the poster, click “View Original” to visit the original website. Except for direct owner posts, HavenNest does not display or intentionally collect/store personal contact details. <br>
                    <strong>Safety:</strong> Beware of scams. Do not send deposits before verification. HavenNest is not responsible for third‑party content, links, or transactions. &copy; 2026 HavenNest App.
                 </div>`,
        insPop: `<h3>Why is Tenant Insurance essential?</h3>
                <p style="color:#166534; font-weight:bold;">It's more than just a landlord's requirement; it's the ultimate safety net for your belongings and financial peace of mind.</p>
                <ul style="text-align:left; line-height:1.8;">
                    <li><strong>Contents Coverage:</strong> Protects your furniture, electronics, and clothing. If loss occurs due to fire or theft, insurance pays based on replacement value.</li>
                    <li><strong>Liability Protection:</strong> Covers legal costs if your negligence causes damage to others (e.g., water leaks or kitchen fires), shielding you from astronomical bills.</li>
                    <li><strong>Visitor Protection:</strong> Covers medical or legal expenses if a visitor is accidentally injured within your rental unit.</li>
                    <li><strong>Additional Living Expenses:</strong> If your home becomes uninhabitable during repairs, insurance covers hotel stays and extra dining costs.</li>
                </ul>`,
        city: "City",
        beds: "Bedrooms",
        budget: "Budget",
        sort: "Sort",
        view: "View",
        viewCard: "Cards",
        viewCompact: "Compact",
        allCities: "All Cities",
        anyBeds: "Any Beds",
        noLimitBudget: "No Limit",
        all: "All",
        any: "Any",
        lowHigh: "Price: Low to High",
        highLow: "Price: High to Low",
        bedsLowHigh: "Beds: Low to High",
        bedsHighLow: "Beds: High to Low",
        dateNewOld: "Date: New to Old",
        default: "Default",
        sourceCrawler: "Crawled",
        sourceOwner: "Direct Post",
        viewDetail: "View Detail",
        contact: "Contact",
        mapNotice: "📍 Friendly Reminder: Some listings may have inexact map locations due to incomplete address data. Please refer to details for accuracy.",
        filterHint: "💡 Tip: Filters applied here will also update the listings shown on the map above."
    }
};

function updateSeoMeta() {
    const d = dict[curLang];
    document.title = d.seoTitle;
    document.documentElement.lang = curLang === 'zh' ? 'zh-CN' : 'en';
    const desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute('content', d.seoDescription);
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) ogTitle.setAttribute('content', d.seoTitle);
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) ogDesc.setAttribute('content', d.seoDescription);
    const twTitle = document.querySelector('meta[name="twitter:title"]');
    if (twTitle) twTitle.setAttribute('content', d.seoTitle);
    const twDesc = document.querySelector('meta[name="twitter:description"]');
    if (twDesc) twDesc.setAttribute('content', d.seoDescription);
}

function normalizeImageUrl(v) {
    if (!v) return '';
    if (typeof v === 'string') return v.trim();
    if (Array.isArray(v)) return normalizeImageUrl(v[0]);
    if (typeof v === 'object' && typeof v.url === 'string') return v.url;
    return '';
}

function getListingImages(i) {
    const imgs = [];
    const a = Array.isArray(i.images) ? i.images : [];
    a.forEach(x => {
        const u = normalizeImageUrl(x);
        if (u && !imgs.includes(u)) imgs.push(u);
    });
    const cover = normalizeImageUrl(i.image);
    if (cover && !imgs.includes(cover)) imgs.unshift(cover);
    return imgs;
}

function sanitizeCrawledDescription(text) {
    if (!text) return '';
    let s = String(text);
    s = s.replace(/\r/g, '');

    s = s.replace(/^\s*(联系人|联系人[:：]|联\s*系\s*人)\s*[:：].*$/gmi, '');
    s = s.replace(/^\s*(电话|联系电话|手机|手机号码|联\s*系\s*电\s*话)\s*[:：].*$/gmi, '');
    s = s.replace(/^\s*(微信|微信号|WeChat|wechat)\s*[:：].*$/gmi, '');
    s = s.replace(/(微信号|微信|WeChat|wechat)\s*[:：]?\s*\n\s*[A-Za-z0-9._-]{5,}\s*$/gmi, '');
    s = s.replace(/^\s*(邮箱|电子邮箱|Email|E-mail)\s*[:：].*$/gmi, '');
    s = s.replace(/^\s*(QQ|WhatsApp|Telegram)\s*[:：].*$/gmi, '');

    s = s.replace(/(\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}/g, '');
    s = s.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '');

    s = s.replace(/http:\\\\+/gi, 'http://');
    s = s.replace(/\bhttp:\/\//gi, 'https://');

    s = s.replace(/\n{3,}/g, '\n\n').trim();
    return s;
}

function toggleFilterPanel() {
    const bar = document.getElementById('filter-bar');
    if (!bar) return;
    bar.classList.toggle('collapsed');
}

function setViewMode(mode) {
    viewMode = (mode === 'compact') ? 'compact' : 'card';
    try { localStorage.setItem('viewMode', viewMode); } catch (e) {}
    renderListings(filteredListings);
}

function getBathsValue(i) {
    const direct = i && (i.baths ?? i.bathrooms ?? i.bath ?? i.ba);
    if (typeof direct === 'number' && Number.isFinite(direct)) return direct;
    if (typeof direct === 'string' && direct.trim()) {
        const n = Number(direct.trim());
        if (Number.isFinite(n)) return n;
    }
    const text = `${i && i.title ? i.title : ''} ${i && i.desc ? i.desc : ''}`.toLowerCase();
    const m = text.match(/(\d+(?:\.\d+)?)\s*(?:bath|baths|ba|卫生间|卫|浴)/);
    if (m) {
        const n = Number(m[1]);
        return Number.isFinite(n) ? n : null;
    }
    return null;
}

const CITY_CENTERS = {
    Vancouver: [49.2827, -123.1207],
    Richmond: [49.1666, -123.1336],
    Burnaby: [49.2488, -122.9805],
    Coquitlam: [49.2830, -122.7932],
    Surrey: [49.1913, -122.8490],
    "Port Coquitlam": [49.2622, -122.7811],
    "Port Moody": [49.2830, -122.8300],
    "New Westminster": [49.2062, -122.9111],
    Delta: [49.0840, -123.0580],
    Langley: [49.1044, -122.6607],
    "Maple Ridge": [49.2195, -122.6019],
    "White Rock": [49.0253, -122.8026]
};

const COMMUNITY_SYNONYMS = {
    "thompson community": "Thompson",
    "thompson community centre": "Thompson",
    "rmd thompson": "Thompson",
    "列治文 thompson": "Thompson",
    "brighouse": "Brighouse",
    "richmond centre": "City Centre",
    "richmond center": "City Centre",
    "city centre": "City Centre",
    "west cambie": "West Cambie",
    "east cambie": "East Cambie",
    "steveston": "Steveston",
    "metrotown": "Metrotown",
    "brentwood": "Brentwood",
    "edmonds": "Edmonds",
    "highgate": "Highgate",
    "ubc": "Point Grey",
    "university of british columbia": "Point Grey",
    "university endowment lands": "Point Grey",
    "coquitlam west": "Coquitlam West",
    "west coquitlam": "Coquitlam West",
    "burquitlam": "Burquitlam",
    "austin heights": "Austin Heights",
    "coquitlam centre": "Coquitlam Centre",
    "coquitlam center": "Coquitlam Centre",
    "whalley (city centre)": "Whalley",
    "white rock (border area)": "White Rock"
};

const COMMUNITY_BBOX = {
    "Richmond||Thompson": [49.145, 49.185, -123.165, -123.105],
    "Richmond||Brighouse": [49.155, 49.175, -123.145, -123.105],
    "Richmond||City Centre": [49.160, 49.185, -123.150, -123.105],
    "Richmond||West Cambie": [49.175, 49.205, -123.190, -123.120],
    "Richmond||East Cambie": [49.175, 49.205, -123.110, -123.055],
    "Richmond||Steveston": [49.115, 49.145, -123.205, -123.145],
    "Burnaby||Metrotown": [49.210, 49.245, -123.030, -122.980],
    "Burnaby||Brentwood": [49.260, 49.285, -123.020, -122.980],
    "Burnaby||Edmonds": [49.205, 49.235, -123.030, -122.950],
    "Burnaby||Highgate": [49.205, 49.230, -123.015, -122.980],
    "Coquitlam||Coquitlam West": [49.240, 49.280, -122.905, -122.840],
    "Coquitlam||Burquitlam": [49.250, 49.290, -122.915, -122.850],
    "Coquitlam||Austin Heights": [49.255, 49.290, -122.870, -122.820],
    "Coquitlam||Coquitlam Centre": [49.265, 49.310, -122.850, -122.770]
};

let DYNAMIC_COMMUNITY_BBOX = {};

function normalizeCommunityName(v) {
    const s = (v || "").toString().trim();
    if (!s) return "";
    const low = s.toLowerCase();
    return COMMUNITY_SYNONYMS[low] || s;
}

function stableU(item, salt) {
    const k = String((item && (item.id || item.url || item.title)) || "");
    const s = `${salt}|${k}`;
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = Math.imul(h, 16777619);
    }
    return (h >>> 0) / 0xFFFFFFFF;
}

function coordsFromBox(item, box) {
    const [latMin, latMax, lngMin, lngMax] = box;
    const u = stableU(item, "lat");
    const v = stableU(item, "lng");
    const lat = latMin + u * (latMax - latMin);
    const lng = lngMin + v * (lngMax - lngMin);
    return [lat, lng];
}

function ensureListingCoords(i) {
    const city = (i && i.city ? String(i.city) : "Vancouver").trim() || "Vancouver";
    const commRaw = (i && (i.community || i.neighborhood || i.area)) ? String(i.community || i.neighborhood || i.area) : "";
    const comm = normalizeCommunityName(commRaw);
    if (city === "Richmond" && comm === "Thompson") {
        const u = stableU(i || {}, "thompson_lat");
        const v = stableU(i || {}, "thompson_lng");
        i.lat = 49.1633 + (u - 0.5) * 0.0022;
        i.lng = -123.1653617 + (v - 0.5) * 0.0022;
        return i;
    }
    if (i && Number.isFinite(Number(i.lat)) && Number.isFinite(Number(i.lng))) return i;
    if (comm) {
        const key = `${city}||${comm}`;
        const key2 = `${city.toLowerCase()}||${comm.toLowerCase()}`;
        const box = COMMUNITY_BBOX[key] || DYNAMIC_COMMUNITY_BBOX[key2];
        if (box) {
            const [lat, lng] = coordsFromBox(i || {}, box);
            i.lat = lat;
            i.lng = lng;
            return i;
        }
    }
    const center = CITY_CENTERS[city] || CITY_CENTERS.Vancouver;
    i.lat = center[0];
    i.lng = center[1];
    return i;
}

async function init() {
    try {
        const stored = localStorage.getItem('viewMode');
        if (stored === 'compact' || stored === 'card') viewMode = stored;
    } catch (e) {}

    const viewSel = document.getElementById('view-mode');
    if (viewSel) viewSel.value = viewMode;

    const bar = document.getElementById('filter-bar');
    if (bar) {
        if (window.innerWidth <= 768) bar.classList.add('collapsed');
    }

    updateUI();

    try {
        const url = new URL(window.location.href);
        pendingListingKey = (url.searchParams.get('listing') || '').toString().trim();
    } catch (e) {}
    
    // 统一从 listings.json 加载所有房源（包括抓取的和屋主发布的）
    try {
        try {
            const bbRes = await fetch('community_bbox_cache.json');
            if (bbRes.ok) {
                const bb = await bbRes.json();
                if (bb && typeof bb === 'object') DYNAMIC_COMMUNITY_BBOX = bb;
            }
        } catch (e) {}
        const res = await fetch('listings.json');
        if (res.ok) {
            const data = await res.json();
            // 房源过滤逻辑：确保至少有标题和价格，坐标如果没有则赋予默认值（兜底）
            allListings = data.map(i => {
                return ensureListingCoords(i);
            });
            try {
                const r = await fetch('/api/public/listings', { method: 'GET' });
                if (r.ok) {
                    const j = await r.json();
                    const owners = Array.isArray(j.listings) ? j.listings : [];
                    const baseOwners = allListings.filter(x => (x.source || '') === 'owner');
                    const baseOwnerMap = {};
                    baseOwners.forEach(x => { if (x && x.id) baseOwnerMap[x.id] = x; });
                    const mergedOwners = owners.map(x => {
                        const existing = x && x.id ? baseOwnerMap[x.id] : null;
                        const merged = existing ? { ...existing, ...x } : { ...x };
                        if ((!merged.lat || !merged.lng) && existing && existing.lat && existing.lng) {
                            merged.lat = existing.lat;
                            merged.lng = existing.lng;
                        }
                        return ensureListingCoords(merged);
                    });
                    allListings = allListings.filter(x => (x.source || '') !== 'owner').concat(mergedOwners);
                }
            } catch (e) {}
            filterListings();
            openListingFromUrlIfNeeded();
        } else {
            console.error('Failed to load listings.json');
        }
    } catch (e) {
        console.warn('Local listings.json not found or invalid. Run crawler.py first.');
    }
}

function getListingKeyFromItem(i) {
    if (i && i.id) return `id:${i.id}`;
    if (i && i.url) return `url:${i.url}`;
    return '';
}

function findListingByKey(key) {
    const k = (key || '').toString().trim();
    if (!k) return null;
    if (k.startsWith('id:')) {
        const id = k.slice(3);
        return allListings.find(x => x && x.id === id) || null;
    }
    if (k.startsWith('url:')) {
        const u = k.slice(4);
        return allListings.find(x => x && x.url === u) || null;
    }
    return allListings.find(x => (x && (x.id === k || x.title === k))) || null;
}

function setListingParam(key, mode) {
    try {
        const url = new URL(window.location.href);
        if (key) url.searchParams.set('listing', key);
        else url.searchParams.delete('listing');
        const m = mode === 'replace' ? 'replaceState' : 'pushState';
        history[m]({ listing: key || '' }, '', url.toString());
    } catch (e) {}
}

function openListingFromUrlIfNeeded() {
    if (!pendingListingKey) return;
    const item = findListingByKey(pendingListingKey);
    if (!item) return;
    showDetail(item, { fromUrl: true });
    pendingListingKey = '';
}

window.addEventListener('popstate', () => {
    let key = '';
    try {
        const url = new URL(window.location.href);
        key = (url.searchParams.get('listing') || '').toString().trim();
    } catch (e) {}
    if (!key) {
        currentListingKey = '';
        closeDetail(true);
        return;
    }
    const item = findListingByKey(key);
    if (item) showDetail(item, { fromUrl: true });
});

function updateLabels() {
    const d = dict[curLang];
    document.getElementById('post-cta-text').innerText = d.postCta;
    document.getElementById('post-btn-text').innerText = d.postBtn;
    const sk = document.getElementById('singlekey-btn');
    if (sk) sk.innerText = d.singleKeyBtn;
    document.getElementById('lang-btn').innerText = curLang === 'zh' ? 'English' : '中文';
    document.getElementById('footer-text').innerHTML = d.footer;
    document.getElementById('map-notice').innerText = d.mapNotice;
    
    // Filter Labels
    document.getElementById('lbl-city').innerText = d.city;
    document.getElementById('lbl-beds').innerText = d.beds;
    document.getElementById('lbl-budget').innerText = d.budget;
    document.getElementById('lbl-sort').innerText = d.sort;
    const lblView = document.getElementById('lbl-view');
    if (lblView) lblView.innerText = d.view;

    const citySel = document.getElementById('filter-city');
    if (citySel && citySel.options && citySel.options.length > 0) {
        citySel.options[0].text = d.allCities;
    }

    const bedsSel = document.getElementById('filter-beds');
    if (bedsSel && bedsSel.options && bedsSel.options.length > 0) {
        bedsSel.options[0].text = d.anyBeds;
        if (bedsSel.options.length > 1) bedsSel.options[1].text = curLang === 'zh' ? '1卧' : '1 BR';
        if (bedsSel.options.length > 2) bedsSel.options[2].text = curLang === 'zh' ? '2卧' : '2 BR';
        if (bedsSel.options.length > 3) bedsSel.options[3].text = curLang === 'zh' ? '3卧' : '3 BR';
        if (bedsSel.options.length > 4) bedsSel.options[4].text = curLang === 'zh' ? '4卧+' : '4+ BR';
    }

    const budgetSel = document.getElementById('filter-budget');
    if (budgetSel && budgetSel.options && budgetSel.options.length > 0) {
        budgetSel.options[0].text = d.noLimitBudget;
    }

    const sortSel = document.getElementById('sort-price');
    if (sortSel && sortSel.options && sortSel.options.length >= 6) {
        sortSel.options[0].text = d.default;
        sortSel.options[1].text = d.lowHigh;
        sortSel.options[2].text = d.highLow;
        sortSel.options[3].text = d.bedsLowHigh;
        sortSel.options[4].text = d.bedsHighLow;
        sortSel.options[5].text = d.dateNewOld;
    }

    const viewSel = document.getElementById('view-mode');
    if (viewSel && viewSel.options && viewSel.options.length >= 2) {
        viewSel.options[0].text = d.viewCard;
        viewSel.options[1].text = d.viewCompact;
    }

    const mapHint = document.getElementById('filter-map-hint');
    if (mapHint) {
        mapHint.innerText = d.filterHint;
    }
}

function updateUI() {
    updateLabels();
    updateSeoMeta();
    const d = dict[curLang];
    const svcs = [
        { k: 'ins', i: '🛡️', t: d.ins },
        { k: 'move', i: '📦', t: d.move },
        { k: 'clean', i: '🧹', t: d.clean }
    ];
    document.getElementById('service-ui').innerHTML = svcs.map(s => `
        <div class="service-item" onclick="openSOP('${s.k}')">
            <div>${s.i}</div>
            <strong>${s.t}</strong>
        </div>
    `).join('');
    
    filterListings();
}

function filterListings() {
    const city = document.getElementById('filter-city').value;
    const beds = parseInt(document.getElementById('filter-beds').value) || 0;
    const budgetValue = document.getElementById('filter-budget').value;
    const budget = budgetValue ? parseInt(budgetValue) : Infinity;
    const sort = document.getElementById('sort-price').value;

    filteredListings = allListings.filter(i => {
        const searchCity = city.toLowerCase();
        const itemCity = (i.city || "").toLowerCase();
        const matchCity = !city || itemCity === searchCity;
        
        // 卧室匹配逻辑
        let matchBeds = true;
        if (beds > 0) {
            if (beds === 4) {
                matchBeds = i.beds >= 4;
            } else {
                matchBeds = i.beds === beds;
            }
        }
        
        // 预算匹配逻辑
        let matchBudget = !budget || i.price <= budget;
        if (i.price === 0) {
            // 如果价格是0且是屋主发布的，认为是“面议”，符合所有预算
            matchBudget = (i.source === 'owner');
        }
        return matchCity && matchBeds && matchBudget;
    });

    const getDateTs = (x) => {
        const s = (x && x.date ? String(x.date) : "").trim();
        const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
        if (!m) return 0;
        const y = Number(m[1]);
        const mo = Number(m[2]) - 1;
        const d = Number(m[3]);
        const ts = Date.UTC(y, mo, d);
        return Number.isFinite(ts) ? ts : 0;
    };

    const priceAsc = (a, b) => {
        const ap = Number(a.price) || 0;
        const bp = Number(b.price) || 0;
        const aUnknown = ap <= 0;
        const bUnknown = bp <= 0;
        if (aUnknown && bUnknown) return 0;
        if (aUnknown) return 1;
        if (bUnknown) return -1;
        return ap - bp;
    };

    const priceDesc = (a, b) => {
        const ap = Number(a.price) || 0;
        const bp = Number(b.price) || 0;
        const aUnknown = ap <= 0;
        const bUnknown = bp <= 0;
        if (aUnknown && bUnknown) return 0;
        if (aUnknown) return 1;
        if (bUnknown) return -1;
        return bp - ap;
    };

    const bedsAsc = (a, b) => (Number(a.beds) || 0) - (Number(b.beds) || 0);
    const bedsDesc = (a, b) => (Number(b.beds) || 0) - (Number(a.beds) || 0);
    const dateNewOld = (a, b) => getDateTs(b) - getDateTs(a);

    const withPromoPin = (cmp) => (a, b) => {
        if (a.isPromo && !b.isPromo) return -1;
        if (!a.isPromo && b.isPromo) return 1;
        return cmp(a, b);
    };

    if (sort === 'low-high') {
        filteredListings.sort(withPromoPin(priceAsc));
    } else if (sort === 'high-low') {
        filteredListings.sort(withPromoPin(priceDesc));
    } else if (sort === 'beds-low-high') {
        filteredListings.sort(withPromoPin(bedsAsc));
    } else if (sort === 'beds-high-low') {
        filteredListings.sort(withPromoPin(bedsDesc));
    } else if (sort === 'date-new-old') {
        filteredListings.sort(withPromoPin(dateNewOld));
    } else {
        const sourcePriority = curLang === 'zh'
            ? { 'VanPeople': 0, 'Rentals.ca': 1, 'Craigslist': 2, 'owner': -1 }
            : { 'Rentals.ca': 0, 'Craigslist': 1, 'VanPeople': 2, 'owner': -1 };

        const getPri = (x) => {
            const k = x.source || '';
            return (k in sourcePriority) ? sourcePriority[k] : 99;
        };

        // 默认排序：屋主/推广房源 (isPromo) 置顶，其次按当前语言偏好排序来源
        filteredListings.sort((a, b) => {
            if (a.isPromo && !b.isPromo) return -1;
            if (!a.isPromo && b.isPromo) return 1;
            const pa = getPri(a);
            const pb = getPri(b);
            if (pa !== pb) return pa - pb;
            return 0;
        });
    }

    renderListings(filteredListings);
}

function renderListings(items) {
    const ui = document.getElementById('listing-ui');
    const d = dict[curLang];
    ui.innerHTML = '';
    
    // Update Map
    map.eachLayer(l => { if (l instanceof L.Marker) map.removeLayer(l); });

    const escapeHtml = (s) => String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const escapeJsStr = (s) => String(s || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\r?\n/g, ' ');

    const normalizeAddrKey = (addr) => {
        let s = (addr || '').toString().trim().toLowerCase();
        if (!s) return '';
        s = s.replace(/^(\d{1,6})\s*-\s*(\d{1,6})\b/, '$2');
        s = s.replace(/\b(?:unit|apt|apartment|suite|ste|#)\s*([a-z0-9-]+)\b/gi, '');
        s = s.replace(/\s+/g, ' ');
        s = s.replace(/[.,]/g, ' ');
        s = s.replace(/\s+/g, ' ').trim();
        return s;
    };

    const sortKey = document.getElementById('sort-price').value;
    const getDateTs = (x) => {
        const s = (x && x.date ? String(x.date) : "").trim();
        const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
        if (!m) return 0;
        const y = Number(m[1]);
        const mo = Number(m[2]) - 1;
        const d = Number(m[3]);
        const ts = Date.UTC(y, mo, d);
        return Number.isFinite(ts) ? ts : 0;
    };

    const cmpForPopup = (a, b) => {
        if (a.isPromo && !b.isPromo) return -1;
        if (!a.isPromo && b.isPromo) return 1;
        const ap = Number(a.price) || 0;
        const bp = Number(b.price) || 0;
        const aUnknown = ap <= 0;
        const bUnknown = bp <= 0;
        const priceAsc = () => {
            if (aUnknown && bUnknown) return 0;
            if (aUnknown) return 1;
            if (bUnknown) return -1;
            return ap - bp;
        };
        const priceDesc = () => {
            if (aUnknown && bUnknown) return 0;
            if (aUnknown) return 1;
            if (bUnknown) return -1;
            return bp - ap;
        };
        if (sortKey === 'low-high') return priceAsc();
        if (sortKey === 'high-low') return priceDesc();
        if (sortKey === 'beds-low-high') return (Number(a.beds) || 0) - (Number(b.beds) || 0);
        if (sortKey === 'beds-high-low') return (Number(b.beds) || 0) - (Number(a.beds) || 0);
        if (sortKey === 'date-new-old') return getDateTs(b) - getDateTs(a);
        return 0;
    };

    const groups = new Map();
    items.forEach(i => {
        const lat = parseFloat(i.lat);
        const lng = parseFloat(i.lng);
        if (isNaN(lat) || isNaN(lng)) return;
        const addrKey = normalizeAddrKey(i.address || '');
        const coordKey = `${lat.toFixed(5)},${lng.toFixed(5)}`;
        const key = `${addrKey || coordKey}|${coordKey}`;
        const g = groups.get(key) || { lat, lng, items: [] };
        g.items.push(i);
        groups.set(key, g);
    });

    const groupList = Array.from(groups.values());
    const coordCounts = {};
    groupList.forEach(g => {
        const lat = parseFloat(g.lat);
        const lng = parseFloat(g.lng);
        const k = `${lat.toFixed(6)},${lng.toFixed(6)}`;
        coordCounts[k] = (coordCounts[k] || 0) + 1;
    });

    groupList.forEach(g => {
        const lat = parseFloat(g.lat);
        const lng = parseFloat(g.lng);
        if (isNaN(lat) || isNaN(lng)) return;
        const k = `${lat.toFixed(6)},${lng.toFixed(6)}`;

        let mLat = lat;
        let mLng = lng;
        if ((coordCounts[k] || 0) > 1) {
            mLat = lat + (Math.random() - 0.5) * 0.0003;
            mLng = lng + (Math.random() - 0.5) * 0.0003;
        }

        const marker = L.marker([mLat, mLng]).addTo(map);

        const sorted = g.items.slice().sort(cmpForPopup);
        const headerAddr = sorted[0] && sorted[0].address ? sorted[0].address : 'Location';
        const header = `<b style="color:var(--primary);">${escapeHtml(headerAddr)}</b>`;
        const countBadge = g.items.length > 1 ? `<div style="font-size:12px; color:#64748b; margin-top:4px;">${g.items.length} ${curLang === 'zh' ? '套房源' : 'listings'}</div>` : '';

        const rows = sorted.map(i => {
            const priceNum = parseFloat(i.price) || 0;
            const displayPrice = priceNum > 0 ? `$${priceNum.toLocaleString()}` : (curLang === 'zh' ? '价格面议' : 'Contact');
            const bedsLabel = i.beds || i.beds === 0 ? `${i.beds}` : '';
            const id = escapeJsStr(i.id || i.title);
            return `
                <div style="display:flex; gap:10px; align-items:flex-start; padding:10px 0; border-top:1px solid #eef2f7;">
                    <div style="flex:1; min-width:0;">
                        <div style="font-weight:800; color:var(--primary);">${escapeHtml(displayPrice)}</div>
                        <div style="font-size:12px; color:#111827; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(i.title || '')}</div>
                        <div style="font-size:11px; color:#64748b;">${escapeHtml(i.city || '')}${bedsLabel !== '' ? ` · ${escapeHtml(bedsLabel)} BR` : ''}</div>
                    </div>
                    <button onclick="window.showDetailById('${id}')" style="background:var(--primary); color:white; border:none; padding:7px 10px; border-radius:8px; font-size:11px; cursor:pointer; white-space:nowrap;">
                        ${d.viewDetail}
                    </button>
                </div>
            `;
        }).join('');

        const listWrapStyle = g.items.length > 4 ? 'max-height:240px; overflow:auto;' : '';
        const popupHtml = `
            <div style="min-width:240px; font-family:sans-serif;">
                ${header}
                ${countBadge}
                <div style="${listWrapStyle} margin-top:10px;">
                    ${rows}
                </div>
            </div>
        `;
        marker.bindPopup(popupHtml);
    });

    // Update Grid
    ui.className = viewMode === 'compact' ? 'grid compact' : 'grid';
    items.forEach(i => {
        const card = document.createElement('div');
        card.className = `card ${viewMode === 'compact' ? 'compact' : ''} ${i.isPromo ? 'gold-frame' : ''}`;
        card.onclick = () => showDetail(i);
        
        const sourceLabel = i.source === 'owner' ? d.sourceOwner : d.sourceCrawler;
        const bedsLabel = i.beds ? `${i.beds} Bed${i.beds > 1 ? 's' : ''}` : '';
        const bathsVal = getBathsValue(i);
        const bathsLabel = bathsVal !== null ? `${bathsVal} Bath${bathsVal > 1 ? 's' : ''}` : '';
        const images = getListingImages(i);
        const displayImage = images[0] || 'logo.svg?v=20260320';
        const priceNum = parseFloat(i.price) || 0;
        const displayPrice = priceNum > 0 ? `$${priceNum.toLocaleString()}` : (curLang === 'zh' ? '价格面议' : 'Contact Owner');
        
        if (viewMode === 'compact') {
            card.innerHTML = `
                <div class="tag">${sourceLabel}</div>
                <div class="card-img" style="background-image:url('${displayImage}')"></div>
                <div class="card-body">
                    <div class="price">${displayPrice}</div>
                    <div class="card-title">${i.title}</div>
                    <div class="card-meta">
                        <span>📍 ${i.city || 'Vancouver'}</span>
                        <span>🛏️ ${bedsLabel}</span>
                        ${bathsLabel ? `<span>🛁 ${bathsLabel}</span>` : ''}
                    </div>
                </div>
            `;
        } else {
            card.innerHTML = `
                <div class="tag">${sourceLabel}</div>
                <div class="card-img" style="background-image:url('${displayImage}')"></div>
                <div class="card-body">
                    <div class="price">${displayPrice}</div>
                    <div class="card-title">${i.title}</div>
                    <div class="card-meta">
                        <span>📍 ${i.city || 'Vancouver'}</span>
                        <span>🛏️ ${bedsLabel}</span>
                    </div>
                </div>
            `;
        }
        ui.appendChild(card);
    });
}

window.showDetailById = (id) => {
    const item = findListingByKey(id);
    if (item) showDetail(item);
};

function showDetail(i, opts) {
    const modal = document.getElementById('detailModal');
    const images = getListingImages(i);
    const d = dict[curLang];
    curSlide = 0;
    const fromUrl = !!(opts && opts.fromUrl);
    const key = getListingKeyFromItem(i);
    if (key) {
        currentListingKey = key;
        if (!fromUrl) setListingParam(key, 'push');
        else setListingParam(key, 'replace');
    }
    
    let galleryContent = images.length > 0 
        ? images.map(img => `<img src="${img}" class="gallery-img">`).join('')
        : `<div class="gallery-img" style="background:#f1f5f9; display:flex; align-items:center; justify-content:center; color:#94a3b8; font-size:1.2rem;">No Image Available</div>`;
    
    // 详情内容处理
    let description = i.desc || i.description || (curLang === 'zh' ? '暂无详细描述。' : 'No detailed description available.');
    if (i.source === 'crawler' || i.source === 'VanPeople' || i.source === 'Craigslist' || i.source === 'Rentals.ca') {
        description = sanitizeCrawledDescription(description);
    }
    const priceNum = parseFloat(i.price) || 0;
    const displayPrice = priceNum > 0 ? `$${priceNum.toLocaleString()}` : (curLang === 'zh' ? '价格面议' : 'Contact Owner');
    
    // 按钮逻辑：抓取房源显示跳转按钮，屋主房源显示联系方式
    let actionButtons = '';
    let contactInfo = '';

    if (i.source === 'crawler' || i.source === 'VanPeople' || i.source === 'Craigslist' || i.source === 'Rentals.ca') {
        // 系统抓取房源：显示跳转原网站按钮 + 租客保险按钮（并排）
        actionButtons = `
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:30px;">
                <button class="btn-action" onclick="window.open('${i.url}', '_blank')" style="background:#475569; margin-top:0;">
                    🌐 ${curLang === 'zh' ? '查看原房源' : 'View Original'}
                </button>
                <button class="btn-action" onclick="closeDetail(); openSOP('ins');" style="margin-top:0;">
                    🛡️ ${curLang === 'zh' ? '申请租客保险' : 'Apply Insurance'}
                </button>
            </div>
        `;
        contactInfo = `<div style="color:#64748b; font-style:italic; font-size:0.9rem;">${curLang === 'zh' ? '提示：此房源由系统抓取，请点击下方按钮跳转原网站查看联系方式。' : 'Note: This listing is sourced by system. Please click the button below to view contact details on the original site.'}</div>`;
    } else {
        // 屋主直发房源：显示联系方式 + 租客保险按钮（下方）
        contactInfo = `
            <div id="contact-info-container" style="background:var(--bg); padding:25px; border-radius:20px; border:1px solid #e2e8f0; text-align:center;">
                <button class="btn-action" style="margin:0; width:auto; padding:10px 30px;" onclick="fetchContact('${i.id}')">
                    🔒 ${curLang === 'zh' ? '点击获取屋主联系方式' : 'Click to View Contact'}
                </button>
            </div>
        `;
        actionButtons = `
            <button class="btn-action" onclick="closeDetail(); openSOP('ins');" style="margin-top:30px;">
                🛡️ ${curLang === 'zh' ? '为此房源申请租客保险' : 'Apply Tenant Insurance'}
            </button>
        `;
    }

    modal.innerHTML = `
        <div class="modal-content" style="text-align:left;">
            <span style="position:absolute; top:20px; right:25px; font-size:40px; color:white; cursor:pointer; z-index:2200; text-shadow:0 0 10px rgba(0,0,0,0.5);" onclick="closeDetail()">×</span>
            <div class="gallery-wrapper">
                ${images.length > 1 ? '<button class="nav-btn nav-prev" onclick="changeSlide(-1)">❮</button><button class="nav-btn nav-next" onclick="changeSlide(1)">❯</button>' : ''}
                <div class="gallery-container" id="gallery-con">${galleryContent}</div>
            </div>
            <div style="padding:40px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h1 style="color:var(--primary); margin:0; font-size:2.5rem;">${displayPrice} / mo</h1>
                    <div style="background:var(--gray-light); padding:8px 15px; border-radius:10px; font-weight:700; color:var(--primary);">
                        ${i.beds || 0} Bedroom${i.beds > 1 ? 's' : ''}
                    </div>
                </div>
                <h2 style="margin:15px 0 25px;">${i.title}</h2>
                <div style="color:#475569; line-height:1.8; font-size:1.1rem; white-space:pre-wrap; margin-bottom:30px;">${description}</div>
                
                ${contactInfo}
                ${actionButtons}
            </div>
        </div>`;
    modal.style.display = 'flex';
}

window.fetchContact = async (id) => {
    const container = document.getElementById('contact-info-container');
    if (!container) return;
    
    container.innerHTML = `<div style="color:#64748b;">${curLang === 'zh' ? '加载中...' : 'Loading...'}</div>`;
    
    try {
        const r = await fetch(`/api/public/contact?id=${encodeURIComponent(id)}`);
        if (r.ok) {
            const data = await r.json();
            if (data.ok) {
                container.innerHTML = `
                    <h3 style="margin-top:0; text-align:left;">${dict[curLang].contact || 'Contact'}:</h3>
                    <div style="font-weight:600; color:var(--primary); text-align:left;">
                        <div>📞 ${data.phone || (curLang === 'zh' ? '未提供' : 'Not Provided')}</div>
                        <div>📧 ${data.email || (curLang === 'zh' ? '未提供' : 'Not Provided')}</div>
                        <div>💬 WeChat: ${data.wechat || (curLang === 'zh' ? '未提供' : 'Not Provided')}</div>
                    </div>
                `;
                return;
            }
        }
    } catch(e) {}
    
    container.innerHTML = `<div style="color:red;">${curLang === 'zh' ? '加载失败，请稍后重试' : 'Failed to load'}</div>`;
};

function changeSlide(dir) {
    const con = document.getElementById('gallery-con');
    if (!con) return;
    const total = con.children.length;
    curSlide = (curSlide + dir + total) % total;
    con.style.transform = `translateX(-${curSlide * 100}%)`;
}

function closeDetail(silent) {
    document.getElementById('detailModal').style.display = 'none';
    if (silent) return;
    if (currentListingKey) {
        currentListingKey = '';
        setListingParam('', 'push');
    }
}
function closeModal() { document.getElementById('svcModal').style.display = 'none'; }

function openSOP(s) {
    activeSvc = s;
    const d = dict[curLang];
    
    document.getElementById('m_t1').innerText = d[s];
    if (s === 'ins') {
        document.getElementById('m_c1').innerHTML = d.insPop;
    } else {
        document.getElementById('m_c1').innerHTML = curLang === 'zh'
            ? `<p style="text-align:left; color:#475569; font-size: 1.05rem; line-height:1.8;">我们提供专业${d[s]}对接服务。请点击下一步填写信息，我们会尽快联系您确认需求并安排报价。</p>`
            : `<p>Professional ${d[s]} services. Click next to leave your details and we’ll follow up shortly.</p>`;
    }
    
    // Inputs placeholders
    document.getElementById('q_name').placeholder = d.name;
    document.getElementById('q_phone').placeholder = d.phone;
    document.getElementById('q_email').placeholder = d.emailLbl;
    document.getElementById('q_dob').placeholder = d.dob;
    document.getElementById('q_eff_date').placeholder = d.eff;
    document.getElementById('q_addr').placeholder = d.addr;
    
    // Buttons
    document.getElementById('btn-next').innerText = d.next;
    document.getElementById('btn-agree').innerText = d.agree;
    document.getElementById('btn-gen').innerText = d.gen;
    document.getElementById('btn-copy').innerText = d.copy;
    document.getElementById('btn-email').innerText = d.email;

    document.getElementById('svcModal').style.display = 'flex';
    nextStep(1);
}

function nextStep(s) {
    document.querySelectorAll('.step').forEach(el => el.classList.remove('active'));
    document.getElementById('step' + s).classList.add('active');
    const d = dict[curLang];
    if (s === 2) {
        document.getElementById('m_t2').innerText = d.m_t2;
        document.getElementById('m_c2').innerText = d.m_c2;
    }
    if (s === 3) document.getElementById('m_t3').innerText = d.m_t3;
    if (s === 4) document.getElementById('m_t4').innerText = d.m_t4;
}

function generateOutput() {
    const v = {
        n: document.getElementById('q_name').value,
        p: document.getElementById('q_phone').value,
        e: document.getElementById('q_email').value,
        a: document.getElementById('q_addr').value,
        dob: document.getElementById('q_dob').value,
        ed: document.getElementById('q_eff_date').value
    };
    
    if (!v.n || !v.p) {
        alert(curLang === 'zh' ? '请填写必要信息' : 'Please fill in required info');
        return;
    }

    document.getElementById('outputBox').value = curLang === 'zh'
        ? `[HavenNest ${activeSvc.toUpperCase()}]\n姓名：${v.n}\n电话：${v.p}\n邮箱：${v.e}\n出生日期：${v.dob}\n生效日期：${v.ed}\n地址：${v.a}`
        : `[HavenNest ${activeSvc.toUpperCase()}]\nName: ${v.n}\nPhone: ${v.p}\nEmail: ${v.e}\nDOB: ${v.dob}\nEffective: ${v.ed}\nAddr: ${v.a}`;
    nextStep(4);
}

function copyText() {
    const box = document.getElementById('outputBox');
    box.select();
    document.execCommand('copy');
    alert(curLang === 'zh' ? '已复制！' : 'Copied!');
}

function openEmail() {
    const body = document.getElementById('outputBox').value;
    const subject = `Inquiry_${activeSvc}_${document.getElementById('q_name').value}`;
    window.location.href = `mailto:support@havennestapp.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function toggleLang() {
    curLang = curLang === 'zh' ? 'en' : 'zh';
    updateUI();
}

// Start
init();
