const API_BASE = (() => {
    const v = new URLSearchParams(location.search).get('api') || '';
    return v.trim().replace(/\/+$/g, '');
})();

function qs(k) {
    return new URLSearchParams(location.search).get(k) || '';
}

function setText(id, t) {
    const el = document.getElementById(id);
    if (el) el.innerText = t;
}

function setPanelVisible(v) {
    document.getElementById('panel').style.display = v ? 'block' : 'none';
}

function getToken() {
    return (document.getElementById('token').value || '').trim();
}

function apiUrl(path) {
    return API_BASE ? `${API_BASE}${path}` : path;
}

async function apiGet(path) {
    const res = await fetch(apiUrl(path), { method: 'GET' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || '请求失败');
    return data;
}

async function apiPatch(path, body) {
    const res = await fetch(apiUrl(path), {
        method: 'PATCH',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || '请求失败');
    return data;
}

async function apiPost(path) {
    const res = await fetch(apiUrl(path), { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || '请求失败');
    return data;
}

function fillForm(listing) {
    document.getElementById('f_title').value = listing.title || '';
    document.getElementById('f_price').value = listing.price || '';
    document.getElementById('f_addr').value = listing.address || '';
    document.getElementById('f_city').value = listing.city || '';
    document.getElementById('f_beds').value = listing.beds === 0 ? 0 : (listing.beds || '');
    document.getElementById('f_desc').value = listing.desc || '';
    setText('statusPill', `状态：${listing.status || 'active'}`);
}

window.loadListing = async () => {
    setText('msg', '');
    setText('panelMsg', '');
    const token = getToken();
    if (!token) {
        setText('msg', '请输入 token');
        return;
    }
    try {
        setText('msg', '加载中…');
        const data = await apiGet(`/api/manage?token=${encodeURIComponent(token)}`);
        fillForm(data.listing || {});
        setPanelVisible(true);
        setText('msg', '已加载');
    } catch (e) {
        setPanelVisible(false);
        const baseHint = !API_BASE
            ? '（当前页面未配置管理 API：请使用最新邮件里的管理链接；或在链接末尾加上 &api=你的Worker地址。Worker地址在 Cloudflare → Workers & Pages → havennest-manage → Triggers 里复制。）'
            : '';
        setText('msg', `${e.message || '加载失败'}${baseHint}`);
    }
};

window.saveListing = async () => {
    setText('panelMsg', '');
    const token = getToken();
    if (!token) return;
    const body = {
        title: document.getElementById('f_title').value,
        price: document.getElementById('f_price').value,
        address: document.getElementById('f_addr').value,
        city: document.getElementById('f_city').value,
        beds: document.getElementById('f_beds').value,
        desc: document.getElementById('f_desc').value
    };
    try {
        setText('panelMsg', '保存中…');
        await apiPatch(`/api/manage?token=${encodeURIComponent(token)}`, body);
        setText('panelMsg', '已保存');
        await window.loadListing();
    } catch (e) {
        setText('panelMsg', e.message || '保存失败');
    }
};

window.setOffline = async () => {
    setText('panelMsg', '');
    const token = getToken();
    if (!token) return;
    try {
        setText('panelMsg', '处理中…');
        await apiPost(`/api/manage?token=${encodeURIComponent(token)}&action=offline`);
        setText('panelMsg', '已下架');
        await window.loadListing();
    } catch (e) {
        setText('panelMsg', e.message || '操作失败');
    }
};

window.setOnline = async () => {
    setText('panelMsg', '');
    const token = getToken();
    if (!token) return;
    try {
        setText('panelMsg', '处理中…');
        await apiPost(`/api/manage?token=${encodeURIComponent(token)}&action=online`);
        setText('panelMsg', '已上架');
        await window.loadListing();
    } catch (e) {
        setText('panelMsg', e.message || '操作失败');
    }
};

window.deleteListing = async () => {
    setText('panelMsg', '');
    const token = getToken();
    if (!token) return;
    const ok = confirm('确认删除此房源？删除后将无法在平台展示。');
    if (!ok) return;
    try {
        setText('panelMsg', '处理中…');
        await apiPost(`/api/manage?token=${encodeURIComponent(token)}&action=delete`);
        setText('panelMsg', '已删除');
        setPanelVisible(false);
    } catch (e) {
        setText('panelMsg', e.message || '操作失败');
    }
};

document.getElementById('token').value = qs('token');
if (qs('token')) window.loadListing();
