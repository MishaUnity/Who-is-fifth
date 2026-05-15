-- depends: 0005.add-is-admin-to-users

-- Пароль: admin1234 (bcrypt hash)
INSERT INTO users (id, username, password_hash, role, is_admin, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin',
    '$2b$12$KIXuCaUkJUHFmJFpFzBgqeJFtYFDMUXDmJjuiLzDHhDwBdK5vkMom',
    'admin',
    true,
    now()
)
ON CONFLICT (id) DO NOTHING;