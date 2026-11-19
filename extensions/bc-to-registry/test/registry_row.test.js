// node --test extensions/bc-to-registry/test
const test = require('node:test');
const assert = require('node:assert/strict');
const R = require('../lib/registry_row.js');

const P = { id: 123, productName: ' 김명월 태안구운감태 1봉 ', storeName: '김명월', salePrice: 11000, discountedSalePrice: 9900,
  discountedRate: 10, commissionRate: 16, shortenUrl: 'https://naver.me/AbC12', reviewInfo: { totalReviewCount: 5 } };

test('검색·발급 주소를 구분하고, 발급은 POST 만 본다', () => {
  const s = 'https://gw-brandconnect.naver.com/affiliate/query/affiliate-products/search-by-query?query=감태&limit=20';
  const i = 'https://gw-brandconnect.naver.com/affiliate/command/affiliate-urls?affiliateProductId=123';
  assert.equal(R.kindOf(s, 'GET'), 'search');
  assert.equal(R.kindOf(i, 'post'), 'issue');
  assert.equal(R.kindOf(i, 'GET'), null);
  assert.equal(R.kindOf('https://gw-brandconnect.naver.com/ping', 'GET'), 'list');   // 0.5.1: 그 밖의 응답은 목록인지 살펴만 본다
  assert.equal(R.productIdOfIssueUrl(i), '123');
});

test('검색 응답 {data, paging} 에서 상품만 꺼낸다', () => {
  assert.deepEqual(R.productsOf({ data: [P, { id: 9 }, null], paging: { nextCursor: 'x' } }).map((p) => p.id), [123]);
  assert.deepEqual(R.productsOf({ data: { data: [P] } }).length, 1);
  assert.deepEqual(R.productsOf({ error: 'x' }), []);
  assert.deepEqual(R.productsOf(null), []);
});

test('발급 응답의 여러 모양에서 링크를 찾고, 쇼핑커넥트 링크가 아니면 버린다', () => {
  assert.equal(R.issuedUrlOf({ shortenUrl: 'https://naver.me/x1' }), 'https://naver.me/x1');
  assert.equal(R.issuedUrlOf({ data: { shortenUrl: 'https://naver.me/x2' } }), 'https://naver.me/x2');
  assert.equal(R.issuedUrlOf({ data: 'https://naver.me/x3' }), 'https://naver.me/x3');
  assert.equal(R.issuedUrlOf({ url: 'https://smartstore.naver.com/a/products/1' }), null);
  assert.equal(R.issuedUrlOf({}), null);
});

test('등록부 행: 판매가=할인 전, 할인가=할인가, 수수료=응답 값 그대로', () => {
  assert.deepEqual(R.toRegistryRow(P, ' 감태 '), {
    keyword: '감태', product_name: '김명월 태안구운감태 1봉', store_name: '김명월', price: 11000, discount_price: 9900,
    commission_rate: '16', link: 'https://naver.me/AbC12', memo: '' });
});

test('할인이 없거나 할인가가 판매가와 같으면 discount_price 는 비운다', () => {
  assert.equal(R.toRegistryRow({ ...P, discountedSalePrice: null }, 'k').discount_price, null);
  assert.equal(R.toRegistryRow({ ...P, discountedSalePrice: 11000 }, 'k').discount_price, null);
  const onlyDisc = R.toRegistryRow({ ...P, salePrice: null }, 'k');
  assert.equal(onlyDisc.price, 9900);
  assert.equal(onlyDisc.discount_price, null);
});

test('검색 화면 주소의 검색어', () => {
  assert.equal(R.keywordFromPageUrl('https://brandconnect.naver.com/971564859961248/affiliate/products/search?keyword=%EA%B0%90%ED%83%9C'), '감태');
  assert.equal(R.keywordFromPageUrl('not a url'), '');
});

test('서버 주소는 이 컴퓨터만', () => {
  assert.ok(R.serverOk('http://localhost:8001'));
  assert.ok(R.serverOk('http://127.0.0.1:8001'));
  assert.ok(!R.serverOk('https://my-tunnel.trycloudflare.com'));
  assert.ok(!R.serverOk('http://localhost.evil.com:8001'));
  assert.ok(!R.serverOk('javascript:alert(1)'));
});

test('수수료는 글자로 — 5 → \'5\', 16.5 → \'16.5\'', () => {
  assert.equal(R.toRegistryRow({ ...P, commissionRate: 5 }, 'k').commission_rate, '5');
  assert.equal(R.toRegistryRow({ ...P, commissionRate: 16.5 }, 'k').commission_rate, '16.5');
  assert.equal(R.toRegistryRow({ ...P, commissionRate: null }, 'k').commission_rate, null);
});

test("'발급 링크 관리' 같은 조회(GET)는 list, 검색·발급과 구분", () => {
  assert.equal(R.kindOf('https://gw-brandconnect.naver.com/affiliate/query/affiliate-urls?page=1', 'GET'), 'list');
  assert.equal(R.kindOf('https://gw-brandconnect.naver.com/affiliate/query/affiliate-products/search-by-query?query=a', 'GET'), 'search');
  assert.equal(R.kindOf('https://gw-brandconnect.naver.com/affiliate/v2/affiliate-urls/search', 'POST'), 'list');   // 조건 붙인 POST 목록
  assert.equal(R.kindOf('https://gw-brandconnect.naver.com/affiliate/command/something', 'POST'), null);              // 명령 응답은 아님
  assert.equal(R.kindOf('https://example.com/affiliate/query/x', 'GET'), null);
});

test('발급 목록: 평평한 모양·한 단계 아래 상품·링크 이름이 달라도 찾는다', () => {
  const flat = { data: [{ id: 1, productName: '사과 5kg', storeName: '농장', salePrice: 30000, commissionRate: 5, shortenUrl: 'https://naver.me/a1' }] };
  const nested = { content: [{ affiliateUrl: 'https://naver.me/b2', createdAt: 'x', affiliateProduct: { id: 7, productName: '배 3kg', storeName: '과수원', discountedSalePrice: 19000, salePrice: 25000, commissionRate: 7 } }] };
  const other = { items: [{ title: '귤 10kg', mallName: '제주', url: 'https://naver.me/c3' }, { title: '광고', url: 'https://example.com/x' }] };
  assert.deepEqual(R.issuedItemsOf(flat).map((p) => [p.productName, p.shortenUrl, p.commissionRate]), [['사과 5kg', 'https://naver.me/a1', 5]]);
  const n = R.issuedItemsOf(nested)[0];
  assert.deepEqual([n.id, n.productName, n.storeName, n.salePrice, n.discountedSalePrice, n.shortenUrl], [7, '배 3kg', '과수원', 25000, 19000, 'https://naver.me/b2']);
  assert.deepEqual(R.issuedItemsOf(other).map((p) => [p.productName, p.storeName]), [['귤 10kg', '제주']]);
  assert.deepEqual(R.issuedItemsOf({ data: [{ id: 1, productName: '링크 없음' }] }), []);
});

test('모양 진단은 열쇠 이름만 남긴다', () => {
  assert.deepEqual(R.shapeOf({ data: { list: [{ a: 1, b: 'x' }] }, total: 3 }), { top: ['data', 'total'], item: ['a', 'b'] });
});

test("리뷰·평점: '리뷰 2,178 · ★4.84', 없으면 '리뷰 없음'", () => {
  assert.equal(R.reviewText({ reviewInfo: { totalReviewCount: 2178, averageReviewScore: 4.8412 } }), '리뷰 2,178 · ★4.84');
  assert.equal(R.reviewText({ reviewInfo: { totalReviewCount: 13, averageReviewScore: null } }), '리뷰 13');
  assert.equal(R.reviewText({ reviewInfo: { totalReviewCount: 0 } }), '리뷰 없음');
  assert.equal(R.reviewText({}), '리뷰 없음');
  const listed = R.issuedItemsOf({ content: [{ affiliateUrl: 'https://naver.me/r1', affiliateProduct: { productName: '감', reviewInfo: { totalReviewCount: 5, averageReviewScore: 4.5 } } }] });
  assert.equal(R.reviewText(listed[0]), '리뷰 5 · ★4.50');
});
