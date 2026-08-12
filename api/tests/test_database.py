import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.database import engine


@pytest.mark.asyncio
async def test_database_uses_test_connection():
    test_database_url = os.environ["TEST_DATABASE_URL"]

    expected_host = make_url(test_database_url).host
    actual_host = engine.url.host

    assert actual_host == expected_host

    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    assert result.scalar_one() == 1