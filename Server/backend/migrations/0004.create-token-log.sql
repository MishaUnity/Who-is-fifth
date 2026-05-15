-- depends: 0002.create-sessions

CREATE TABLE IF NOT EXISTS token_log (
    id          BIGSERIAL   PRIMARY KEY,
    session_id  TEXT        NOT NULL,
    user_id     TEXT,
    tokens_used INTEGER     NOT NULL DEFAULT 0,
    endpoint    TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_token_log_user_id    ON token_log(user_id);
CREATE INDEX IF NOT EXISTS idx_token_log_created_at ON token_log(created_at);