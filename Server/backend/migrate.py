from yoyo import read_migrations, get_backend
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aisa:aisa@localhost:5432/aisa")

backend = get_backend(DATABASE_URL)
migrations = read_migrations("migrations")

with backend.lock():
    backend.apply_migrations(backend.to_apply(migrations))

print("Migrations applied.")