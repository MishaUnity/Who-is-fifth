-- depends: 0001.create-users

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT        PRIMARY KEY,
    user_id     TEXT        REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);