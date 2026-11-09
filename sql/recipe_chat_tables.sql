-- Recipe conversation storage (PostgreSQL). Safe to run repeatedly: IF NOT EXISTS only,
-- no DROP/ALTER, existing rows are never touched.
--
-- recipe_followup_state / recipe_material_review are the existing recipe_session tables.
-- Their columns here are exactly the ones app/services/recipe_session/*.py reads and writes.
-- If the tables already exist (local dashboard_db), these statements do nothing; check them with
--   python -m scripts.recipe_chat_db check
-- recipe_chat_session is new: per-session conversation state with optimistic revision.
-- recipe_easy_view (2026-10-29): cached AI "쉽게 보기" per recipe source version and prompt version.
-- recipe_ai_image (2026-10-29): AI dish image for recipes without a source photo (labelled on the card).

CREATE TABLE IF NOT EXISTS public.recipe_followup_state (
    session_id     TEXT        NOT NULL,
    ingredient_id  TEXT        NOT NULL,
    context_key    TEXT        NOT NULL,
    state_json     TEXT        NOT NULL,
    revision       INTEGER     NOT NULL CHECK (revision >= 1),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS public.recipe_material_review (
    session_id       TEXT        NOT NULL,
    ingredient_id    TEXT        NOT NULL,
    answer_revision  INTEGER     NOT NULL,
    context_key      TEXT        NOT NULL,
    review_json      TEXT        NOT NULL,
    revision         INTEGER     NOT NULL CHECK (revision >= 1),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, ingredient_id, answer_revision, context_key)
);

CREATE TABLE IF NOT EXISTS public.recipe_chat_session (
    session_id  TEXT        PRIMARY KEY,
    state_json  TEXT        NOT NULL,
    revision    INTEGER     NOT NULL CHECK (revision >= 1),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.recipe_easy_view (
    recipe_id       TEXT        NOT NULL,
    content_hash    TEXT        NOT NULL,
    prompt_version  TEXT        NOT NULL,
    view_json       TEXT        NOT NULL,
    model           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipe_id, content_hash, prompt_version)
);

CREATE TABLE IF NOT EXISTS public.recipe_ai_image (
    recipe_id       TEXT        NOT NULL,
    content_hash    TEXT        NOT NULL,
    prompt_version  TEXT        NOT NULL,
    mime            TEXT        NOT NULL,
    image           BYTEA       NOT NULL,
    model           TEXT,
    prompt          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipe_id, content_hash, prompt_version)
);
