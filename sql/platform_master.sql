-- =====================================================
-- Commerce AI Platform Master v2 Migration
-- 기존 platform_master 보존 + 확장
-- =====================================================

ALTER TABLE platform_master
ADD COLUMN IF NOT EXISTS parent_platform TEXT;

ALTER TABLE platform_master
ADD COLUMN IF NOT EXISTS base_domain TEXT;

ALTER TABLE platform_master
ADD COLUMN IF NOT EXISTS crawler_type TEXT DEFAULT 'pending';

ALTER TABLE platform_master
ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100;

ALTER TABLE platform_master
ADD COLUMN IF NOT EXISTS category_strength TEXT;

ALTER TABLE platform_master
ADD COLUMN IF NOT EXISTS memo TEXT;

ALTER TABLE platform_master
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- 기존 base_url 값을 base_domain으로 보정
UPDATE platform_master
SET base_domain = base_url
WHERE base_domain IS NULL
  AND base_url IS NOT NULL;

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_platform_master_active
ON platform_master(is_active);

CREATE INDEX IF NOT EXISTS idx_platform_master_priority
ON platform_master(priority);

-- 초기 플랫폼 등록/업데이트
INSERT INTO platform_master (
    platform_code,
    platform_name,
    parent_platform,
    base_url,
    base_domain,
    crawler_type,
    is_active,
    priority,
    category_strength,
    memo,
    updated_at
)
VALUES
(
    'naver',
    '네이버쇼핑',
    'naver',
    'https://shopping.naver.com',
    'shopping.naver.com',
    'api_or_search',
    TRUE,
    10,
    '가격비교, 검색 기반, 다양한 판매처',
    'Commerce AI 핵심 플랫폼',
    NOW()
),
(
    'coupang',
    '쿠팡',
    'coupang',
    'https://www.coupang.com',
    'www.coupang.com',
    'crawler_pending',
    TRUE,
    20,
    '빠른배송, 리뷰 데이터',
    '상품 상세 수집 예정',
    NOW()
),
(
    'kurly',
    '컬리',
    'kurly',
    'https://www.kurly.com',
    'www.kurly.com',
    'crawler_pending',
    TRUE,
    30,
    '프리미엄 식품, 신선식품',
    '품질 비교 플랫폼',
    NOW()
),
(
    'emart',
    '이마트몰',
    'ssg',
    'https://emart.ssg.com',
    'emart.ssg.com',
    'crawler_pending',
    TRUE,
    40,
    '대형마트, 신선식품, 장보기',
    'SSG.COM 내 이마트몰 채널',
    NOW()
),
(
    'epost',
    '우체국쇼핑',
    'epost',
    'https://mall.epost.go.kr',
    'mall.epost.go.kr',
    'selenium',
    TRUE,
    50,
    '농산물, 지역특산물, 공공몰',
    '기존 수집기 운영중',
    NOW()
)
ON CONFLICT (platform_code)
DO UPDATE SET
    platform_name = EXCLUDED.platform_name,
    parent_platform = EXCLUDED.parent_platform,
    base_url = EXCLUDED.base_url,
    base_domain = EXCLUDED.base_domain,
    crawler_type = EXCLUDED.crawler_type,
    is_active = EXCLUDED.is_active,
    priority = EXCLUDED.priority,
    category_strength = EXCLUDED.category_strength,
    memo = EXCLUDED.memo,
    updated_at = NOW();
