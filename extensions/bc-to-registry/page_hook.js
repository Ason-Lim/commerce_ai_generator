// 페이지(MAIN world)에서 브랜드커넥트가 스스로 부른 응답을 '읽기만' 해서 콘텐츠 스크립트로 넘긴다 (2026-11-19).
// 이 파일은 어떤 요청도 새로 보내지 않는다: 원래 fetch/XHR 를 그대로 통과시키고 응답 사본(clone)만 읽는다.
(function () {
  'use strict';
  if (window.__bcToRegistryHooked) return;
  window.__bcToRegistryHooked = true;
  console.info('[bc-to-registry] 응답 읽기 준비', location.pathname);

  const TAG = 'bc-to-registry';
  // 브랜드커넥트 서버(gw-brandconnect)에서 오는 응답은 모두 사본을 '읽기만' 한다 (0.5.1).
  // '발급 링크 관리' 목록이 어떤 주소·방식(GET/POST)으로 오는지 몰라서 넓게 본다. 요청은 새로 보내지 않는다.
  const WATCH = /^https:\/\/gw-brandconnect\.naver\.com\//;

  function send(url, method, text) {
    if (!text) return;
    let json;
    try { json = JSON.parse(text); } catch (e) { return; }
    window.postMessage({ source: TAG, url: String(url), method: String(method || 'GET').toUpperCase(), json }, location.origin);
  }

  const origFetch = window.fetch;
  window.fetch = function (input, init) {
    const p = origFetch.apply(this, arguments);
    try {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      const method = (init && init.method) || (input && input.method) || 'GET';
      if (WATCH.test(url)) {
        p.then((res) => { if (res && res.ok) res.clone().text().then((t) => send(url, method, t)).catch(() => {}); })
          .catch(() => {});
      }
    } catch (e) { /* 읽기 실패는 페이지 동작에 영향 없음 */ }
    return p;
  };

  const XHR = XMLHttpRequest.prototype;
  const origOpen = XHR.open;
  const origSend = XHR.send;
  XHR.open = function (method, url) {
    this.__bcReg = WATCH.test(String(url)) ? { method, url } : null;
    return origOpen.apply(this, arguments);
  };
  XHR.send = function () {
    if (this.__bcReg) {
      const info = this.__bcReg;
      this.addEventListener('load', function () {
        try {
          if (this.status < 200 || this.status >= 300) return;
          const t = (this.responseType === '' || this.responseType === 'text') ? this.responseText
            : (this.responseType === 'json' ? JSON.stringify(this.response) : '');
          send(info.url, info.method, t);
        } catch (e) { /* 무시 */ }
      });
    }
    return origSend.apply(this, arguments);
  };
})();
