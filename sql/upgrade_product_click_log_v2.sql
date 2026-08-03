ALTER TABLE product_click_log
ADD COLUMN IF NOT EXISTS product_id TEXT;

ALTER TABLE product_click_log
ADD COLUMN IF NOT EXISTS rank INTEGER;

ALTER TABLE product_click_log
ADD COLUMN IF NOT EXISTS platform TEXT;

ALTER TABLE product_click_log
ADD COLUMN IF NOT EXISTS mall_name TEXT;

ALTER TABLE product_click_log
ADD COLUMN IF NOT EXISTS price NUMERIC;

ALTER TABLE product_click_log
ADD COLUMN IF NOT EXISTS clicked_at TIMESTAMP DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_product_click_log_mode
ON product_click_log(recommendation_mode);

CREATE INDEX IF NOT EXISTS idx_product_click_log_clicked_at
ON product_click_log(clicked_at);
