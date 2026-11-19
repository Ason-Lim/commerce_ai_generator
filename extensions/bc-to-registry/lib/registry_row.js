// 브랜드커넥트 응답 → commerce_ai 등록부 행 (순수 함수, 2026-11-19)
// 확장(콘텐츠 스크립트)과 node 테스트가 같은 파일을 쓴다. 네트워크·DOM 을 건드리지 않는다.
(function (root) {
  'use strict';

  const SEARCH_RE = /\/affiliate\/query\/affiliate-products\/search-by-query/;
  const ISSUE_RE = /\/affiliate\/command\/affiliate-urls/;

  /** 페이지가 부른 주소가 어떤 응답인지: 'search' | 'issue' | null */
  function kindOf(url, method) {
    const u = String(url || '');
    if (SEARCH_RE.test(u)) return 'search';
    if (ISSUE_RE.test(u) && String(method || 'GET').toUpperCase() === 'POST') return 'issue';
    return null;
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
      commission_rate: Number.isFinite(comm) ? comm : null,
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

  const api = { kindOf, productsOf, issuedUrlOf, productIdOfIssueUrl, keywordFromPageUrl, toRegistryRow, serverOk };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BcRegistry = api;
})(typeof self !== 'undefined' ? self : this);
