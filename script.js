let allListings = [];
let filteredListings = [];
let curLang = 'zh';
let curSlide = 0;
let activeSvc = '';
let map = L.map('map', { scrollWheelZoom: false }).setView([49.24, -123.05], 11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const dict = {
    zh: {
        seoTitle: "HavenNest 安家居 | 大温全量房源聚合 & 一站式租房服务门户",
        seoDescription: "HavenNest 聚合大温各大平台房源，为您提供省时省心的全方位租房支持。从专业持牌团队提供的一站式租客保险咨询，到搬家、清洁对接，全程为您把控细节，让您的温哥华迁居之旅省心无忧。",
        postCta: "拥有空置房源？免费发布至平台 / Have a vacancy?",
        postBtn: "屋主发布 / Post Now",
        singleKeyBtn: "SingleKey 背调",
        next: "明白，下一步 / Next Step",
        agree: "同意授权并继续 / Agree & Authorize",
        gen: "生成正式申请表 / Generate Application",
        copy: "复制文本 / Copy",
        email: "调起邮件发送 / Email",
        name: "您的姓名 / Full Name",
        phone: "联系电话 / Phone",
        emailLbl: "电子邮箱 / Email",
        dob: "出生日期 / Date of Birth (YYYY-MM-DD)",
        eff: "保单生效日期 / Effective Date (YYYY-MM-DD)",
        addr: "房源具体地址 / Address",
        m_t2: "授权告知 / Authorization",
        m_c2: "作为大温专业持牌专家团队，我们承诺保护您的隐私。本人授权 HavenNest 将提供的信息安全地转交给我们的合作经纪进行报价。您的隐私受 BC 法律保护。",
        m_t3: "申请信息填写 / Application Details",
        m_t4: "表单生成成功 / Form Generated",
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
        beds: "卧室",
        budget: "预算",
        sort: "排序",
        all: "全部",
        any: "不限",
        lowHigh: "价格从低到高",
        default: "默认",
        sourceCrawler: "系统抓取",
        sourceOwner: "屋主直发",
        viewDetail: "查看详情",
        contact: "联系方式",
        mapNotice: "📍 温馨提示：部分抓取房源因原网站地址信息不全，地图定位可能存在偏差，请以详情页描述为准。"
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
        all: "All",
        any: "Any",
        lowHigh: "Price: Low to High",
        default: "Default",
        sourceCrawler: "Crawled",
        sourceOwner: "Direct Post",
        viewDetail: "View Detail",
        contact: "Contact",
        mapNotice: "📍 Friendly Reminder: Some listings may have inexact map locations due to incomplete address data. Please refer to details for accuracy."
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

async function init() {
    updateUI();
    
    // 统一从 listings.json 加载所有房源（包括抓取的和屋主发布的）
    try {
        const res = await fetch('listings.json');
        if (res.ok) {
            const data = await res.json();
            // 房源过滤逻辑：确保至少有标题和价格，坐标如果没有则赋予默认值（兜底）
            allListings = data.map(i => {
                if (!i.lat || !i.lng) {
                    i.lat = 49.2827;
                    i.lng = -123.1207;
                }
                return i;
            });
            try {
                const r = await fetch('/api/public/listings', { method: 'GET' });
                if (r.ok) {
                    const j = await r.json();
                    const owners = Array.isArray(j.listings) ? j.listings : [];
                    const nonOwners = allListings.filter(x => (x.source || '') !== 'owner');
                    owners.forEach(x => {
                        if (!x.lat || !x.lng) {
                            x.lat = 49.2827;
                            x.lng = -123.1207;
                        }
                    });
                    allListings = nonOwners.concat(owners);
                }
            } catch (e) {}
            filterListings();
        } else {
            console.error('Failed to load listings.json');
        }
    } catch (e) {
        console.warn('Local listings.json not found or invalid. Run crawler.py first.');
    }
}

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
        // 增强城市匹配：检查城市字段、地址字段以及标题
        const searchCity = city.toLowerCase();
        const itemCity = (i.city || "").toLowerCase();
        const itemAddr = (i.address || "").toLowerCase();
        const itemTitle = (i.title || "").toLowerCase();

        const matchCity = !city || 
                         itemCity.includes(searchCity) || 
                         itemAddr.includes(searchCity) || 
                         itemTitle.includes(searchCity);
        
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

    if (sort === 'low-high') {
        filteredListings.sort((a, b) => (a.price || 0) - (b.price || 0));
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
    
    // 增加随机偏移量以解决 Marker 重叠问题
    items.forEach(i => {
        const lat = parseFloat(i.lat);
        const lng = parseFloat(i.lng);
        if (isNaN(lat) || isNaN(lng)) return;

        // 为每个点增加微小的随机偏移 (约 10-20 米)，防止完全重叠
        const offsetLat = lat + (Math.random() - 0.5) * 0.0003;
        const offsetLng = lng + (Math.random() - 0.5) * 0.0003;

        const marker = L.marker([offsetLat, offsetLng]).addTo(map);
        
        const popupHtml = `
            <div style="min-width:200px; font-family:sans-serif;">
                <b style="color:var(--primary);">${i.address || 'Location'}</b>
                <hr style="border:0; border-top:1px solid #eee; margin:10px 0;">
                <div style="margin-bottom:12px;">
                    <span style="color:var(--primary); font-weight:800; font-size:1.1rem;">$${i.price || 'Contact'}</span>
                    <div style="font-size:12px; color:#666; margin:2px 0;">${i.title}</div>
                    <button onclick="window.showDetailById('${i.id || i.title}')" 
                        style="background:var(--primary); color:white; border:none; padding:6px 12px; border-radius:6px; font-size:11px; cursor:pointer; width:100%;">
                        ${d.viewDetail}
                    </button>
                </div>
            </div>`;
        marker.bindPopup(popupHtml);
    });

    // Update Grid
    items.forEach(i => {
        const card = document.createElement('div');
        card.className = `card ${i.isPromo ? 'gold-frame' : ''}`;
        card.onclick = () => showDetail(i);
        
        const sourceLabel = i.source === 'owner' ? d.sourceOwner : d.sourceCrawler;
        const bedsLabel = i.beds ? `${i.beds} Bed${i.beds > 1 ? 's' : ''}` : '';
        const images = getListingImages(i);
        const displayImage = images[0] || 'logo.svg?v=20260320';
        const priceNum = parseFloat(i.price) || 0;
        const displayPrice = priceNum > 0 ? `$${priceNum.toLocaleString()}` : (curLang === 'zh' ? '价格面议' : 'Contact Owner');
        
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
        ui.appendChild(card);
    });
}

window.showDetailById = (id) => {
    const item = allListings.find(x => (x.id === id || x.title === id));
    if (item) showDetail(item);
};

function showDetail(i) {
    const modal = document.getElementById('detailModal');
    const images = getListingImages(i);
    const d = dict[curLang];
    curSlide = 0;
    
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
            <div style="background:var(--bg); padding:25px; border-radius:20px; border:1px solid #e2e8f0;">
                <h3 style="margin-top:0;">${d.contact}:</h3>
                <div style="font-weight:600; color:var(--primary);">
                    <div>📞 ${i.phone || '房东未提供 / Not Provided'}</div>
                    <div>📧 ${i.email || '房东未提供 / Not Provided'}</div>
                </div>
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

function changeSlide(dir) {
    const con = document.getElementById('gallery-con');
    if (!con) return;
    const total = con.children.length;
    curSlide = (curSlide + dir + total) % total;
    con.style.transform = `translateX(-${curSlide * 100}%)`;
}

function closeDetail() { document.getElementById('detailModal').style.display = 'none'; }
function closeModal() { document.getElementById('svcModal').style.display = 'none'; }

function openSOP(s) {
    activeSvc = s;
    const d = dict[curLang];
    
    document.getElementById('m_t1').innerText = d[s];
    document.getElementById('m_c1').innerHTML = s === 'ins' ? d.insPop : `<p>Professional ${d[s]} services.</p>`;
    
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

    document.getElementById('outputBox').value = `[HavenNest ${activeSvc.toUpperCase()}]\nName: ${v.n}\nPhone: ${v.p}\nEmail: ${v.e}\nDOB: ${v.dob}\nEffective: ${v.ed}\nAddr: ${v.a}`;
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
