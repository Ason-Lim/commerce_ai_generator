// 서비스 워커: commerce_ai 관리자 API 로만 요청한다 (2026-11-19). 브랜드커넥트 API 는 부르지 않는다.
importScripts('lib/registry_row.js');
const R = self.BcRegistry;
const DEFAULTS = { server: 'http://localhost:8001', token: '' };

async function settings() {
  const s = await chrome.storage.local.get(DEFAULTS);
  return { server: String(s.server || DEFAULTS.server).replace(/\/+$/, ''), token: String(s.token || '') };
}

async function call(path, init) {
  const s = await settings();
  if (!R.serverOk(s.server)) return { ok: false, error: '서버 주소는 이 컴퓨터(localhost)만 쓸 수 있어요 — ⚙에서 고쳐 주세요' };
  if (!s.token) return { ok: false, error: '관리자 토큰이 없어요 — ⚙에서 넣어 주세요' };
  let res;
  try {
    res = await fetch(s.server + path, {
      ...init,
      headers: { 'Content-Type': 'application/json', 'X-Access-Token': s.token, ...((init && init.headers) || {}) },
    });
  } catch (e) {
    return { ok: false, error: `commerce_ai 서버(${s.server})에 닿지 않아요 — 켜져 있는지 확인해 주세요` };
  }
  if (res.status === 401) return { ok: false, error: '관리자 토큰이 맞지 않아요 — ⚙에서 확인해 주세요' };
  let body = null;
  try { body = await res.json(); } catch (e) { /* 본문 없음 */ }
  if (!res.ok) return { ok: false, error: (body && body.detail && String(body.detail)) || `서버 오류 ${res.status}` };
  return { ok: true, body };
}

async function handle(msg) {
  if (msg.type === 'LIST') {
    const r = await call('/admin/api/connect/links', { method: 'GET' });
    if (!r.ok) return r;
    const items = (r.body && r.body.items) || [];
    return { ok: true, count: r.body.count ?? items.length, links: items.map((x) => (x['쇼핑커넥트 링크'] || '').trim()).filter(Boolean) };
  }
  if (msg.type === 'SAVE') {
    const row = msg.row || {};
    if (!row.link || !row.product_name) return { ok: false, error: '상품명·링크가 없어요' };
    const r = await call('/admin/api/connect/links', { method: 'POST', body: JSON.stringify({ rows: [row] }) });
    if (!r.ok) return r;
    return { ok: true, added: r.body.added, rejected: r.body.rejected || [] };
  }
  if (msg.type === 'OPEN_OPTIONS') {
    chrome.runtime.openOptionsPage();
    return { ok: true };
  }
  return { ok: false, error: '모르는 요청' };
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // 브랜드커넥트 탭의 우리 콘텐츠 스크립트에서 온 요청만 받는다
  const from = (sender && sender.url) || '';
  if (sender.id !== chrome.runtime.id || !/^https:\/\/brandconnect\.naver\.com\//.test(from)) {
    sendResponse({ ok: false, error: '허용되지 않은 곳에서 온 요청' });
    return false;
  }
  handle(msg || {}).then(sendResponse, (e) => sendResponse({ ok: false, error: String(e) }));
  return true;
});
