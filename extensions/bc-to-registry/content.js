// 브랜드커넥트 화면: 사람이 발급한 링크를 버튼 한 번으로 commerce_ai 등록부에 저장 (2026-11-19).
// 정책 선: 브랜드커넥트 검색·발급 API 를 스스로 부르지 않는다(page_hook 이 페이지 응답만 읽음), 버튼 한 번 = 한 상품.
(function () {
  'use strict';
  const R = self.BcRegistry;
  const TAG = 'bc-to-registry';
  // 콘솔에서 'bc-to-registry' 로 걸러 보면 확장이 무엇을 잡았는지 보인다 (토큰·링크 외 개인 정보는 남기지 않음)
  const log = (...a) => console.info('[bc-to-registry]', ...a);
  log('시작', location.pathname);

  const state = {
    products: new Map(),   // id → 상품 (최근 검색 응답)
    issuedNow: [],         // 이 화면에서 사람이 방금 발급한 상품 id (최근 것이 앞)
    registered: new Set(), // 등록부에 이미 있는 링크
    keyword: '',
    keywordTouched: false, // 사람이 키워드 칸을 고쳤으면 검색어로 덮어쓰지 않는다
    msg: {},               // id → {kind, text}
    server: { ok: null, text: '' },
    open: true,
  };

  // ── 페이지 응답 받기 ──
  window.addEventListener('message', (ev) => {
    if (ev.source !== window || !ev.data || ev.data.source !== TAG) return;
    const { url, method, json } = ev.data;
    const kind = R.kindOf(url, method);
    if (kind === 'search') {
      let q = '';
      try { q = (new URL(url, location.href).searchParams.get('query') || '').trim(); } catch (e) {}
      if (q && !state.keywordTouched) state.keyword = q;
      const got = R.productsOf(json);
      for (const p of got) state.products.set(String(p.id), p);
      log('검색 응답', q, got.length + '개', '발급된 것', got.filter((p) => p.shortenUrl).length + '개');
      render();
    } else if (kind === 'list') {
      // '발급 링크 관리' 같은 화면: 이미 발급한 링크 목록 → 등록부에 없는 것을 위로 (0.5.0)
      const got = R.issuedItemsOf(json);
      if (!got.length) { log('조회 응답 (발급 링크 없음)', method, new URL(url, location.href).pathname, JSON.stringify(R.shapeOf(json))); return; }
      for (const p of got) {
        const prev = state.products.get(String(p.id));
        state.products.set(String(p.id), prev ? { ...p, ...prev, shortenUrl: prev.shortenUrl || p.shortenUrl } : p);
      }
      log('발급 목록 응답', new URL(url, location.href).pathname, got.length + '개');
      render();
    } else if (kind === 'issue') {
      const id = R.productIdOfIssueUrl(url);
      const link = R.issuedUrlOf(json);
      log('발급 응답', id, link || '(링크를 못 찾음 — 응답 모양: ' + Object.keys(json || {}).join(',') + ')');
      if (id && link) {
        const p = state.products.get(String(id)) || { id, productName: '' };
        p.shortenUrl = link;
        state.products.set(String(id), p);
        state.issuedNow = [String(id), ...state.issuedNow.filter((x) => x !== String(id))];
        state.open = true;
        render();
      }
    }
  });

  // ── 백그라운드와 대화 ──
  function ask(msg) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(msg, (res) => resolve(res || { ok: false, error: chrome.runtime.lastError?.message || '응답 없음' }));
      } catch (e) {
        resolve({ ok: false, error: '확장이 다시 로드됐어요. 이 탭을 새로고침해 주세요.' });
      }
    });
  }

  async function loadRegistered() {
    const res = await ask({ type: 'LIST' });
    if (res.ok) {
      state.registered = new Set(res.links);
      state.server = { ok: true, text: `등록부 ${res.count}건` };
    } else {
      state.server = { ok: false, text: res.error };
    }
    render();
  }

  async function save(id) {
    const p = state.products.get(id);
    if (!p || !p.shortenUrl) return;
    const kw = state.keyword.trim();
    if (!kw) { state.msg[id] = { kind: 'err', text: '키워드를 먼저 적어 주세요' }; render(); return; }
    state.msg[id] = { kind: 'wait', text: '저장 중…' };
    render();
    const res = await ask({ type: 'SAVE', row: R.toRegistryRow(p, kw) });
    if (res.ok && res.added === 1) {
      state.registered.add(p.shortenUrl);
      state.msg[id] = { kind: 'ok', text: `저장했어요 (키워드 '${kw}')` };
      loadRegistered();                      // 위쪽 '등록부 N건' 을 새로
    } else if (res.ok) {
      const why = (res.rejected && res.rejected[0] && res.rejected[0].reason) || '저장되지 않았어요';
      if (why === '이미 등록된 링크예요') state.registered.add(p.shortenUrl);
      state.msg[id] = { kind: 'err', text: why };
    } else {
      state.msg[id] = { kind: 'err', text: res.error };
    }
    render();
  }

  // ── 화면 ──
  const won = (n) => (n == null ? '' : Number(n).toLocaleString('ko-KR') + '원');
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function linkedIds() {
    // 방금 발급한 것 → 등록부에 아직 없는 발급 링크 → 이미 저장된 것 순서
    const rest = [...state.products.values()].filter((p) => p.shortenUrl && !state.issuedNow.includes(String(p.id)));
    const missing = rest.filter((p) => !state.registered.has(p.shortenUrl)).map((p) => String(p.id));
    const saved = rest.filter((p) => state.registered.has(p.shortenUrl)).map((p) => String(p.id));
    return [...state.issuedNow, ...missing, ...saved].slice(0, 80);
  }

  function summary() {
    const linked = [...state.products.values()].filter((p) => p.shortenUrl);
    if (!linked.length) return '';
    const missing = linked.filter((p) => !state.registered.has(p.shortenUrl)).length;
    return `<div class="bcr-sum">이 화면의 발급 링크 ${linked.length}개 · <b>등록부에 없는 것 ${missing}개</b></div>`;
  }

  function rowHtml(id) {
    const p = state.products.get(id);
    const row = R.toRegistryRow(p, state.keyword);
    const saved = state.registered.has(p.shortenUrl);
    const m = state.msg[id];
    const fresh = state.issuedNow.includes(id);
    return `<li class="bcr-item${fresh ? ' bcr-fresh' : ''}">
      <div class="bcr-name">${fresh ? '<b class="bcr-new">방금 발급</b> ' : ''}${esc(row.product_name || '(상품명 모름 — 검색 결과에서 다시 찾아 주세요)')}</div>
      <div class="bcr-meta">${esc(row.store_name)} · ${row.discount_price ? `<s>${won(row.price)}</s> ${won(row.discount_price)}` : won(row.price)}
        · 수수료 ${row.commission_rate == null ? '?' : row.commission_rate + '%'} · <span class="bcr-rev">${esc(R.reviewText(p))}</span>
        · <span class="bcr-link">${esc(row.link)}</span></div>
      <div class="bcr-act">
        ${saved ? '<span class="bcr-saved">저장됨 ✓</span>'
          : `<button class="bcr-save" data-id="${esc(id)}" ${row.product_name ? '' : 'disabled'}>등록부에 저장</button>`}
        ${m ? `<span class="bcr-msg bcr-${m.kind}">${esc(m.text)}</span>` : ''}
      </div></li>`;
  }

  function panel() {
    let el = document.getElementById('bcr-panel');
    if (!el) {
      el = document.createElement('div');
      el.id = 'bcr-panel';
      // body 가 아니라 <html> 에 붙인다: 브랜드커넥트(React)가 body 를 다시 그려도 지워지지 않게
      document.documentElement.appendChild(el);
      log('창을 붙였어요');
      dragSetup(el);
      el.addEventListener('click', (e) => {
        if (drag.justMoved) { drag.justMoved = false; e.preventDefault(); e.stopPropagation(); return; }   // 옮긴 뒤 손을 뗀 '클릭'은 무시
        const b = e.target.closest('button');
        if (!b) return;
        if (b.classList.contains('bcr-save')) save(b.dataset.id);
        else if (b.classList.contains('bcr-toggle')) { state.open = !state.open; render(); }
        else if (b.classList.contains('bcr-reload')) loadRegistered();
        else if (b.classList.contains('bcr-options')) ask({ type: 'OPEN_OPTIONS' });
      });
      el.addEventListener('input', (e) => {
        if (e.target.classList.contains('bcr-kw')) { state.keyword = e.target.value; state.keywordTouched = true; }
      });
    }
    return el;
  }

  // ── 창 옮기기 (0.7.0): 머리줄을 길게(0.35초) 누르면 끌어서 옮긴다. 위치는 저장돼 다음에도 그 자리. 머리줄 두 번 누르면 처음 자리로 ──
  const POS = self.BcPanelPos;
  const POS_KEY = 'bcr_panel_pos';
  const drag = { timer: null, on: false, start: null, offset: null, justMoved: false };

  function placeAt(el, pos) {
    if (!POS.valid(pos)) { el.style.left = el.style.top = ''; el.style.right = el.style.bottom = ''; return; }
    const r = el.getBoundingClientRect();
    const p = POS.clamp(pos, { width: r.width || 380, height: r.height || 200 }, { width: innerWidth, height: innerHeight });
    Object.assign(el.style, { left: p.left + 'px', top: p.top + 'px', right: 'auto', bottom: 'auto' });
  }

  function savePos(pos) { try { chrome.storage.local.set({ [POS_KEY]: pos }); } catch (e) { log('위치 저장 실패', e); } }

  function dragSetup(el) {
    try { chrome.storage.local.get(POS_KEY, (v) => placeAt(el, v && v[POS_KEY])); } catch (e) {}
    const cancel = () => { clearTimeout(drag.timer); drag.timer = null; };
    el.addEventListener('pointerdown', (e) => {
      if (!e.target.closest('.bcr-head') || e.button !== 0) return;
      if (e.target.closest('.bcr-reload, .bcr-options')) return;
      drag.start = { x: e.clientX, y: e.clientY };
      cancel();
      drag.timer = setTimeout(() => {
        const r = el.getBoundingClientRect();
        drag.on = true;
        drag.offset = { x: drag.start.x - r.left, y: drag.start.y - r.top };
        el.classList.add('bcr-dragging');
        try { el.setPointerCapture(e.pointerId); } catch (err) {}
      }, POS.HOLD_MS);
    });
    el.addEventListener('pointermove', (e) => {
      if (drag.timer && !drag.on && POS.moved(drag.start, { x: e.clientX, y: e.clientY })) cancel();
      if (!drag.on) return;
      e.preventDefault();
      placeAt(el, { left: e.clientX - drag.offset.x, top: e.clientY - drag.offset.y });
    });
    const end = () => {
      cancel();
      if (!drag.on) return;
      drag.on = false;
      drag.justMoved = true;
      el.classList.remove('bcr-dragging');
      const r = el.getBoundingClientRect();
      savePos({ left: r.left, top: r.top });
      setTimeout(() => { drag.justMoved = false; }, 400);
    };
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
    el.addEventListener('dblclick', (e) => {
      if (!e.target.closest('.bcr-head') || e.target.closest('button:not(.bcr-toggle)')) return;
      placeAt(el, null);
      try { chrome.storage.local.remove(POS_KEY); } catch (err) {}
    });
    addEventListener('resize', () => {
      if (el.style.left) placeAt(el, { left: parseFloat(el.style.left), top: parseFloat(el.style.top) });
    });
  }

  function render() {
    const el = panel();
    const ids = linkedIds();
    const focused = document.activeElement && document.activeElement.classList.contains('bcr-kw');
    if (focused) { renderList(el, ids); return; }   // 키워드 입력 중에는 입력칸을 다시 그리지 않는다
    el.className = state.open ? 'bcr-open' : 'bcr-closed';
    el.innerHTML = `
      <div class="bcr-head">
        <button class="bcr-toggle" title="눌러서 접기/펴기 · 길게 눌러 옮기기 · 두 번 눌러 처음 자리로">commerce_ai 등록부 ${state.open ? '▾' : '▸'}</button>
        <span class="bcr-server ${state.server.ok === false ? 'bcr-err' : ''}">${esc(state.server.text || '')}</span>
        <button class="bcr-reload" title="등록부 다시 읽기">↻</button>
        <button class="bcr-options" title="서버 주소·관리자 토큰">⚙</button>
      </div>
      <div class="bcr-body">
        <label>키워드 <input class="bcr-kw" value="${esc(state.keyword)}" maxlength="60" placeholder="검색하면 검색어가 들어와요"></label>
        <div class="bcr-sumwrap"></div>
        <ul class="bcr-list"></ul>
      </div>`;
    renderList(el, ids);
  }

  function renderList(el, ids) {
    const ul = el.querySelector('.bcr-list');
    if (!ul) return;
    const sum = el.querySelector('.bcr-sumwrap');
    if (sum) sum.innerHTML = summary();
    ul.innerHTML = ids.length ? ids.map(rowHtml).join('')
      : '<li class="bcr-empty">상품을 검색하고 \'링크 발급\'을 누르면 여기에 나와요. 예전에 발급한 링크를 한꺼번에 맞추려면 위쪽 \'발급 링크 관리\' 화면을 여세요.</li>';
  }

  // 확장이 다시 로드되면 옛 패널이 남지 않게
  document.getElementById('bcr-panel')?.remove();
  render();
  loadRegistered();
  // 화면이 다시 그려지며 창이 지워지면 다시 붙인다
  setInterval(() => { if (!document.getElementById('bcr-panel')) { log('창이 지워져서 다시 붙여요'); render(); } }, 1500);
})();
