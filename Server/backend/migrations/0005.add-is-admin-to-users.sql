-- depends: 0001.create-users

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT false;

-- Индекс пригодится для фильтрации в админке
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);