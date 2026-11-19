// 브랜드커넥트 응답 → commerce_ai 등록부 행 (순수 함수, 2026-11-19)
// 확장(콘텐츠 스크립트)과 node 테스트가 같은 파일을 쓴다. 네트워크·DOM 을 건드리지 않는다.
(function (root) {
  'use strict';

  const SEARCH_RE = /\/affiliate\/query\/affiliate-products\/search-by-query/;
  const ISSUE_RE = /\/affiliate\/command\/affiliate-urls/;

  const QUERY_RE = /\/affiliate\/query\//;
  const LINK_RE = /^https:\/\/(naver\.me|[\w.-]*brandconnect\.naver\.com)\//;

  /** 페이지가 부른 주소가 어떤 응답인지: 'search' | 'issue' | 'list' | null
   *  'list' = 그 밖의 조회(GET) 응답 — 예: '발급 링크 관리' 화면의 발급 목록 (0.5.0) */
  function kindOf(url, method) {
    const u = String(url || '');
    const m = String(method || 'GET').toUpperCase();
    if (SEARCH_RE.test(u)) return 'search';
    if (ISSUE_RE.test(u) && m === 'POST') return 'issue';
    if (QUERY_RE.test(u) && m === 'GET' && /^https:\/\/gw-brandconnect\.naver\.com\//.test(u)) return 'list';
    // 0.5.1: 그 밖의 브랜드커넥트 서버 응답도 '발급 링크가 든 목록'인지 살펴본다 (예: 조건을 붙여 POST 로 받는 목록)
    if (/^https:\/\/gw-brandconnect\.naver\.com\//.test(u) && !/\/command\//.test(u)) return 'list';
    return null;
  }

  const pick = (o, keys) => { for (const k of keys) if (o && o[k] != null && o[k] !== '') return o[k]; return null; };
  const NAME_KEYS = ['productName', 'name', 'title'];
  const LINK_KEYS = ['shortenUrl', 'affiliateUrl', 'shortUrl', 'url'];

  /** 응답 어디에 있든 '상품명 + 발급 링크(naver.me·brandconnect)'를 가진 것을 찾아 상품 모양으로 맞춘다.
   *  상품 정보가 한 단계 아래(예: {affiliateProduct:{…}, shortenUrl})에 있어도 찾는다. 모양을 모르는 화면용. */
  function issuedItemsOf(resp) {
    const out = [];
    const seen = new Set();
    const visit = (o, depth) => {
      if (!o || typeof o !== 'object' || depth > 6) return;
      if (Array.isArray(o)) { o.forEach((x) => visit(x, depth + 1)); return; }
      const kids = Object.values(o).filter((v) => v && typeof v === 'object' && !Array.isArray(v));
      const link = [o, ...kids].map((x) => pick(x, LINK_KEYS)).find((v) => typeof v === 'string' && LINK_RE.test(v.trim()));
      const holder = [o, ...kids].find((x) => typeof pick(x, NAME_KEYS) === 'string');
      if (link && holder && !seen.has(link.trim())) {
        seen.add(link.trim());
        const f = (keys) => pick(holder, keys) ?? pick(o, keys);
        out.push({ id: f(['id', 'affiliateProductId', 'productId']) ?? link.trim(), productName: pick(holder, NAME_KEYS),
          storeName: f(['storeName', 'mallName', 'channelName']), salePrice: f(['salePrice', 'price']),
          discountedSalePrice: f(['discountedSalePrice', 'discountPrice']), commissionRate: f(['commissionRate']),
          shortenUrl: link.trim() });
        return;
      }
      Object.values(o).forEach((v) => visit(v, depth + 1));
    };
    visit(resp, 0);
    return out;
  }

  /** 모양 진단용: 응답의 윗단 열쇠와 첫 목록 원소의 열쇠 (값은 남기지 않는다) */
  function shapeOf(resp) {
    const top = resp && typeof resp === 'object' ? Object.keys(resp) : [];
    let first = null;
    const find = (o, d) => { if (first || !o || typeof o !== 'object' || d > 4) return;
      if (Array.isArray(o)) { if (o[0] && typeof o[0] === 'object') first = Object.keys(o[0]); return; }
      Object.values(o).forEach((v) => find(v, d + 1)); };
    find(resp, 0);
    return { top, item: first };
  }

  /** 검색 응답 {data:[...], paging} → 상품 목록 (모양이 다르면 빈 목록) */
  function productsOf(resp) {
    const d = resp && (Array.isArray(resp.data) ? resp.data
      : (resp.data && Array.isArray(resp.data.data) ? resp.data.data : null));
    return (d || []).filter((p) => p && p.id != null && p.productName);
  }

  /** 발급 응답에서 링크 — 응답 모양이 여러 가지라 아는 이름을 차례로 본다 */
  function issuedUrlOf(resp) {
    const d = resp || {};
    const cand = [d.shortenUrl, d.data && d.data.shortenUrl, d.url, d.affiliateUrl, d.shortUrl,
      d.data && d.data.url, d.data && d.data.affiliateUrl, typeof d.data === 'string' ? d.data : null];
    for (const c of cand) {
      if (typeof c === 'string' && /^https:\/\/(naver\.me|[\w.-]*brandconnect\.naver\.com)\//.test(c.trim())) return c.trim();
    }
    return null;
  }

  /** 발급 주소의 ?affiliateProductId= */
  function productIdOfIssueUrl(url) {
    const m = String(url || '').match(/[?&]affiliateProductId=([^&#]+)/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  /** 브랜드커넥트 검색 화면 주소의 검색어 */
  function keywordFromPageUrl(url) {
    try {
      const q = new URL(url).searchParams;
      return (q.get('keyword') || q.get('query') || q.get('searchKeyword') || '').trim();
    } catch (e) {
      return '';
    }
  }

  function num(v) {
    if (v == null || v === '') return null;
    const n = Number(String(v).replace(/[^\d.]/g, ''));
    return Number.isFinite(n) && n > 0 ? n : null;
  }

  /** 상품 + 키워드 → POST /admin/api/connect/links 의 rows[0]
   *  price = 할인 전 판매가(salePrice), discount_price = 할인가(discountedSalePrice, 판매가보다 쌀 때만). */
  function toRegistryRow(p, keyword, link) {
    const sale = num(p.salePrice);
    const disc = num(p.discountedSalePrice);
    const hasDisc = disc != null && (sale == null || disc < sale);
    const comm = p.commissionRate == null ? null : Number(p.commissionRate);
    return {
      keyword: String(keyword || '').trim().slice(0, 60),
      product_name: String(p.productName || '').trim().slice(0, 200),
      store_name: String(p.storeName || '').trim().slice(0, 80),
      price: sale != null ? sale : (disc != null ? disc : null),
      discount_price: hasDisc && sale != null ? disc : null,
      // 글자로 보낸다: 숫자 5 를 보내면 서버가 '5.0' 으로 적는다 (등록부 다른 줄은 '5')
      commission_rate: Number.isFinite(comm) ? String(comm) : null,
      link: String(link || p.shortenUrl || '').trim(),
      memo: '',
    };
  }

  /** 서버 주소 점검: 이 컴퓨터(localhost·127.0.0.1)만 허용 — 토큰이 밖으로 나가지 않게 */
  function serverOk(base) {
    try {
      const u = new URL(base);
      return (u.protocol === 'http:' || u.protocol === 'https:') && ['localhost', '127.0.0.1'].includes(u.hostname);
    } catch (e) {
      return false;
    }
  }

  const api = { kindOf, issuedItemsOf, shapeOf, productsOf, issuedUrlOf, productIdOfIssueUrl, keywordFromPageUrl, toRegistryRow, serverOk };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BcRegistry = api;
})(typeof self !== 'undefined' ? self : this);
