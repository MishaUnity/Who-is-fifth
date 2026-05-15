-- depends: 0002.create-sessions

CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL   PRIMARY KEY,
    session_id  TEXT        NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content     TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);