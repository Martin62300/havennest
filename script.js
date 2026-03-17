const CONFIG = {
    token: 'pat2AFw6PJ7WRwGTy.11c7c578063429d1757a89ca9abb523e122370c8f13ede3990c7b090bde6b364',
    baseId: 'appfs8aXtirNbrbWa',
    tableName: 'Table 1'
};

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
        postCta: "拥有空置房源？免费发布至平台 / Have a vacancy?",
        postBtn: "屋主发布",
        next: "明白，下一步",
        agree: "同意授权并继续",
        gen: "生成正式申请表",
        copy: "复制文本 / Copy",
        email: "调起邮件发送 / Email",
        name: "您的姓名 / Full Name",
        phone: "联系电话 / Phone",
        emailLbl: "电子邮箱 / Email",
        dob: "出生日期 (YYYY-MM-DD)",
        eff: "保单生效日期 (YYYY-MM-DD)",
        addr: "房源具体地址 / Address",
        m_t2: "授权告知 / Authorization",
        m_c2: "作为大温专业持牌专家团队，我们承诺保护您的隐私。本人授权 HavenNest 将提供的信息安全地转交给我们的合作经纪进行报价。您的隐私受 BC 法律保护。",
        m_t3: "申请信息填写",
        m_t4: "表单生成成功",
        ins: "租客保险咨询",
        move: "专业搬家服务",
        clean: "退房清洁服务",
        footer: "免责声明：房源包含系统抓取及屋主发布。&copy; 2026 HavenNest App.",
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
        contact: "联系方式"
    },
    en: {
        postCta: "Have a vacancy? Post it on HavenNest for free!",
        postBtn: "Post Now",
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
        footer: "Disclaimer: Sourced from crawlers and direct posts. &copy; 2026 HavenNest App.",
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
        contact: "Contact"
    }
};

async function init() {
    updateUI();
    
    // 1. Load Crawled Listings (Local JSON)
    try {
        const res = await fetch('listings.json');
        if (res.ok) {
            const crawledData = await res.json();
            // 过滤掉没有坐标的房源，并统一数据格式
            const validItems = crawledData.filter(i => i.lat && i.lng).map(i => ({
                ...i,
                id: i.id || i.title,
                source: "crawler"
            }));
            allListings = [...allListings, ...validItems];
            filterListings();
        }
    } catch (e) {
        console.warn('Local listings.json not found or invalid. Run crawler.py first.');
    }

    // 2. Fetch Airtable Listings (Remote API)
    const url = `https://api.airtable.com/v0/${CONFIG.baseId}/${encodeURIComponent(CONFIG.tableName)}`;
    try {
        const res = await fetch(url, { headers: { Authorization: `Bearer ${CONFIG.token}` } });
        const data = await res.json();
        
        for (const r of data.records) {
            const f = r.fields;
            const addr = f['房源具体地址 (Address)'] || "Vancouver";
            const title = f['房源标题 (Listing Title)'] || "Rental Listing";
            const photos = f['房源照片 / Property Photos'] ? f['房源照片 / Property Photos'].map(p => p.url) : [];
            
            let city = f['所在城市 (City)'] || "";
            if (!city) {
                const searchStr = (title + " " + addr).toLowerCase();
                if (searchStr.includes('richmond') || searchStr.includes('列治文') || searchStr.includes('lansdowne')) {
                    city = "Richmond";
                } else {
                    city = "Vancouver";
                }
            }

            let beds = parseInt(f['卧室数量 (Beds)']);
            if (isNaN(beds) || beds === 0) {
                const searchStr = (title + " " + (f['房源描述 (Description)'] || "")).toLowerCase();
                const bedMatch = searchStr.match(/(\d+)\s*(室|房|br|bed|bedroom)/);
                beds = (bedMatch && bedMatch[1]) ? parseInt(bedMatch[1]) : 1;
            }

            // 如果 Airtable 里没有坐标，默认给一个温哥华市中心的坐标，防止报错
            const lat = parseFloat(f['Latitude']) || 49.2827;
            const lng = parseFloat(f['Longitude']) || -123.1207;

            const item = {
                id: r.id, 
                source: "owner",
                title: title,
                price: typeof f['月租金 (Monthly Rent)'] === 'number' ? f['月租金 (Monthly Rent)'] : (parseInt(String(f['月租金 (Monthly Rent)']).replace(/[^\d]/g, '')) || 0),
                isPromo: f['推广级别 (Promotion)'] && f['推广级别 (Promotion)'].includes('限时免费推广'),
                images: photos, 
                image: photos[0] || "",
                desc: f['房源描述 (Description)'] || "No description.",
                lat: lat,
                lng: lng,
                address: addr,
                phone: f['联系电话 (Phone)'], 
                email: f['电子邮箱 (Email)'],
                beds: beds,
                city: city
            };
            
            allListings.push(item);
            filterListings();
        }
    } catch (e) {
        console.error('Airtable fetch failed', e);
    }
}

function updateLabels() {
    const d = dict[curLang];
    document.getElementById('post-cta-text').innerText = d.postCta;
    document.getElementById('post-btn-text').innerText = d.postBtn;
    document.getElementById('lang-btn').innerText = curLang === 'zh' ? 'English' : '中文';
    document.getElementById('footer-text').innerHTML = d.footer;
    
    // Filter Labels
    document.getElementById('lbl-city').innerText = d.city;
    document.getElementById('lbl-beds').innerText = d.beds;
    document.getElementById('lbl-budget').innerText = d.budget;
    document.getElementById('lbl-sort').innerText = d.sort;

    // Filter Options (Dynamic update would be better, but static is fine for now)
}

function updateUI() {
    updateLabels();
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
        const matchBudget = !budget || i.price <= budget || i.price === 0; // 0通常代表价格面议
        return matchCity && matchBeds && matchBudget;
    });

    if (sort === 'low-high') {
        filteredListings.sort((a, b) => (a.price || 0) - (b.price || 0));
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
        
        card.innerHTML = `
            <div class="tag">${sourceLabel}</div>
            <div class="card-img" style="background-image:url('${i.image}')"></div>
            <div class="card-body">
                <div class="price">$${i.price.toLocaleString()}</div>
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
    if (i.source === "crawler" && i.url) {
        window.open(i.url, '_blank');
        return;
    }
    
    const modal = document.getElementById('detailModal');
    const images = (i.images && i.images.length > 0) ? i.images : [i.image];
    const d = dict[curLang];
    curSlide = 0;
    
    let galleryContent = images.map(img => `<img src="${img}" class="gallery-img">`).join('');
    
    modal.innerHTML = `
        <div class="modal-content" style="text-align:left;">
            <span style="position:absolute; top:20px; right:25px; font-size:40px; color:white; cursor:pointer; z-index:2200; text-shadow:0 0 10px rgba(0,0,0,0.5);" onclick="closeDetail()">×</span>
            <div class="gallery-wrapper">
                ${images.length > 1 ? '<button class="nav-btn nav-prev" onclick="changeSlide(-1)">❮</button><button class="nav-btn nav-next" onclick="changeSlide(1)">❯</button>' : ''}
                <div class="gallery-container" id="gallery-con">${galleryContent}</div>
            </div>
            <div style="padding:40px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h1 style="color:var(--primary); margin:0; font-size:2.5rem;">$${i.price.toLocaleString()} / mo</h1>
                    <div style="background:var(--gray-light); padding:8px 15px; border-radius:10px; font-weight:700; color:var(--primary);">
                        ${i.beds} Bedroom${i.beds > 1 ? 's' : ''}
                    </div>
                </div>
                <h2 style="margin:15px 0 25px;">${i.title}</h2>
                <div style="color:#475569; line-height:1.8; font-size:1.1rem; white-space:pre-wrap; margin-bottom:30px;">${i.desc}</div>
                
                <div style="background:var(--bg); padding:25px; border-radius:20px; border:1px solid #e2e8f0;">
                    <h3 style="margin-top:0;">${d.contact}:</h3>
                    <div style="font-weight:600; color:var(--primary);">
                        <div>📞 ${i.phone || '房东未提供 / Not Provided'}</div>
                        <div>📧 ${i.email || '房东未提供 / Not Provided'}</div>
                    </div>
                </div>
                
                <button class="btn-action" onclick="closeDetail(); openSOP('ins');" style="margin-top:30px;">
                    🛡️ 为此房源申请租客保险 / Apply Insurance
                </button>
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
