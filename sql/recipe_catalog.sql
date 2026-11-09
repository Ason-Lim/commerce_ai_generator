-- Public recipe catalogue (food-safety COOKRCP01 · EPIS · Nongsaro), read by the chat.
-- Loaded by: python -m scripts.import_recipe_catalog --json <recipes.json> --apply
-- IF NOT EXISTS only; rows are never deleted by the import.
CREATE TABLE IF NOT EXISTS public.recipe_catalog (
    recipe_id     TEXT        PRIMARY KEY,
    source        TEXT        NOT NULL,
    name          TEXT        NOT NULL,
    payload       JSONB       NOT NULL,
    content_hash  TEXT        NOT NULL,
    imported_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS recipe_catalog_name_idx ON public.recipe_catalog (name);
