from __future__ import annotations

from collections.abc import Generator

import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    """Fixture to provide a PostgreSQL container for testing."""
    with PostgresContainer("postgres:15.3") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_connection(postgres_container) -> str:
    """Fixture to provide a database connection string."""
    return postgres_container.get_connection_url()
