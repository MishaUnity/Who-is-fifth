-- depends:

CREATE TABLE IF NOT EXISTS users (
    id          TEXT        PRIMARY KEY,
    username    TEXT        UNIQUE NOT NULL,
    password_hash TEXT      NOT NULL,
    role        TEXT        NOT NULL DEFAULT 'user',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);