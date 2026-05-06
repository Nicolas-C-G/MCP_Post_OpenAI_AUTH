from collections.abc import Sequence
from typing import Any

import asyncpg

from app.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.settings.postgres_host,
                port=self.settings.postgres_port,
                database=self.settings.postgres_db,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
                min_size=1,
                max_size=5,
                command_timeout=15,
            )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        await self.connect()
        assert self._pool is not None
        async with self._pool.acquire() as connection:
            rows: Sequence[asyncpg.Record] = await connection.fetch(query, *args)
        return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        await self.connect()
        assert self._pool is not None
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
        return dict(row) if row is not None else None

    async def execute_check(self) -> bool:
        await self.connect()
        assert self._pool is not None
        async with self._pool.acquire() as connection:
            value = await connection.fetchval("SELECT 1")
        return value == 1
