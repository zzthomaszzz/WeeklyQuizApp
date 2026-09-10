import os
# Unit tests never connect to the application database.
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/test"
os.environ["SESSION_SECRET"] = "unit-test-secret-that-is-at-least-32-characters"
os.environ["COOKIE_SECURE"] = "false"
