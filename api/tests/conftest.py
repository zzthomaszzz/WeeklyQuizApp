import os
from pathlib import Path

from dotenv import load_dotenv


API_DIR = Path(__file__).resolve().parent.parent
TEST_ENV_FILE = API_DIR / ".env.test"

load_dotenv(TEST_ENV_FILE)

test_database_url = os.getenv("TEST_DATABASE_URL")

if not test_database_url:
    raise RuntimeError(
        "TEST_DATABASE_URL is missing. Add it to api/.env.test"
    )

# Force the application to use the test database during pytest
os.environ["DATABASE_URL"] = test_database_url
