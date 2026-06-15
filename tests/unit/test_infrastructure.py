"""
Stage 03 Infrastructure Tests — PostgreSQL & Redis Connectivity.

These tests verify that the Docker services are reachable from Python
before the database layer is built in Stage 04.

Prerequisites:
    docker compose -f docker/docker-compose.yml up -d

Run with:
    pytest tests/unit/test_infrastructure.py -v
"""

import asyncio

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# PostgreSQL Connectivity Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPostgresConnectivity:
    @pytest.mark.asyncio
    async def test_postgres_accepts_connections(self):
        """
        Verify that asyncpg can open a connection to the running
        PostgreSQL container on localhost:5432.
        """
        import asyncpg

        from aitester.core.config import settings

        # asyncpg uses its own URL format (no +asyncpg driver prefix)
        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        try:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
        finally:
            await conn.close()

    @pytest.mark.asyncio
    async def test_postgres_correct_database_exists(self):
        """
        Verify that the `aitester` database exists and is accessible.
        """
        import asyncpg

        from aitester.core.config import settings

        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        try:
            db_name = await conn.fetchval("SELECT current_database()")
            assert db_name == "aitester"
        finally:
            await conn.close()

    @pytest.mark.asyncio
    async def test_postgres_correct_user(self):
        """
        Verify that the connected user matches the configured user.
        """
        import asyncpg

        from aitester.core.config import settings

        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        try:
            user = await conn.fetchval("SELECT current_user")
            assert user == "aitester"
        finally:
            await conn.close()

    @pytest.mark.asyncio
    async def test_postgres_version_is_16(self):
        """
        Verify that PostgreSQL version 16.x is running.
        """
        import asyncpg

        from aitester.core.config import settings

        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        try:
            version_str = await conn.fetchval("SHOW server_version")
            major_version = int(version_str.split(".")[0])
            assert major_version >= 16, f"Expected PG 16+, got: {version_str}"
        finally:
            await conn.close()

    @pytest.mark.asyncio
    async def test_postgres_can_create_and_drop_table(self):
        """
        Verify that the aitester user has DDL privileges (CREATE/DROP TABLE).
        """
        import asyncpg

        from aitester.core.config import settings

        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        try:
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS _aitester_infra_test (id serial PRIMARY KEY)"
            )
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = '_aitester_infra_test'"
            )
            assert count == 1
        finally:
            await conn.execute("DROP TABLE IF EXISTS _aitester_infra_test")
            await conn.close()

    @pytest.mark.asyncio
    async def test_postgres_supports_jsonb(self):
        """
        Verify JSONB is available (used extensively for test payloads and results).
        """
        import asyncpg

        from aitester.core.config import settings

        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        try:
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS _jsonb_test (data jsonb)"
            )
            await conn.execute(
                "INSERT INTO _jsonb_test VALUES ($1::jsonb)",
                '{"key": "value", "count": 42}',
            )
            result = await conn.fetchval("SELECT data->>'key' FROM _jsonb_test")
            assert result == "value"
        finally:
            await conn.execute("DROP TABLE IF EXISTS _jsonb_test")
            await conn.close()

    @pytest.mark.asyncio
    async def test_postgres_concurrent_connections(self):
        """
        Verify that multiple concurrent asyncpg connections work without errors.
        This validates the pool will work correctly in Stage 04.
        """
        import asyncpg

        from aitester.core.config import settings

        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

        async def single_query(n: int) -> int:
            conn = await asyncpg.connect(url)
            result = await conn.fetchval("SELECT $1::int", n)
            await conn.close()
            return result  # type: ignore[return-value]

        results = await asyncio.gather(*[single_query(i) for i in range(10)])
        assert list(results) == list(range(10))


# ─────────────────────────────────────────────────────────────────────────────
# Redis Connectivity Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestRedisConnectivity:
    @pytest.fixture
    async def redis_client(self):
        """Provide a connected Redis client, cleaned up after the test."""
        import redis.asyncio as aioredis

        from aitester.core.config import settings

        client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        yield client
        await client.aclose()

    @pytest.mark.asyncio
    async def test_redis_responds_to_ping(self, redis_client):
        """
        Verify the Redis container is up and responding to PING.
        """
        pong = await redis_client.ping()
        assert pong is True

    @pytest.mark.asyncio
    async def test_redis_set_and_get(self, redis_client):
        """
        Verify basic SET/GET operations work correctly.
        """
        await redis_client.set("aitester:infra:test", "hello_stage03", ex=10)
        value = await redis_client.get("aitester:infra:test")
        assert value == "hello_stage03"

    @pytest.mark.asyncio
    async def test_redis_key_expiry(self, redis_client):
        """
        Verify that keys with TTL actually expire (TTL is readable immediately).
        """
        await redis_client.set("aitester:ttl:test", "expires_soon", ex=60)
        ttl = await redis_client.ttl("aitester:ttl:test")
        assert 0 < ttl <= 60

    @pytest.mark.asyncio
    async def test_redis_delete_key(self, redis_client):
        """
        Verify DEL removes a key and subsequent GET returns None.
        """
        await redis_client.set("aitester:delete:test", "to_be_deleted")
        await redis_client.delete("aitester:delete:test")
        value = await redis_client.get("aitester:delete:test")
        assert value is None

    @pytest.mark.asyncio
    async def test_redis_increment(self, redis_client):
        """
        Verify INCR works — used for rate limiting and run counters.
        """
        key = "aitester:counter:test"
        await redis_client.delete(key)
        val1 = await redis_client.incr(key)
        val2 = await redis_client.incr(key)
        val3 = await redis_client.incr(key)
        assert [val1, val2, val3] == [1, 2, 3]
        await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_redis_json_roundtrip(self, redis_client):
        """
        Verify JSON data can be stored and retrieved correctly.
        Used for caching parsed specs and run summaries.
        """
        import json

        payload = {
            "run_id": "test-123",
            "status": "completed",
            "total_tests": 42,
            "security_score": 87.5,
        }
        key = "aitester:cache:run:test-123"
        await redis_client.set(key, json.dumps(payload), ex=30)
        raw = await redis_client.get(key)
        recovered = json.loads(raw)  # type: ignore[arg-type]
        assert recovered["run_id"] == "test-123"
        assert recovered["security_score"] == 87.5
        await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_redis_server_info(self, redis_client):
        """
        Verify that Redis server info is accessible and version is 7+.
        """
        info = await redis_client.info("server")
        version = info["redis_version"]
        major = int(version.split(".")[0])
        assert major >= 7, f"Expected Redis 7+, got: {version}"

    @pytest.mark.asyncio
    async def test_redis_concurrent_operations(self, redis_client):
        """
        Verify concurrent SET operations work without race conditions.
        """
        import json

        keys = [f"aitester:concurrent:test:{i}" for i in range(20)]

        async def set_key(k: str, v: int) -> None:
            await redis_client.set(k, json.dumps(v), ex=10)

        await asyncio.gather(*[set_key(k, i) for i, k in enumerate(keys)])

        results = []
        for i, k in enumerate(keys):
            val = await redis_client.get(k)
            results.append(json.loads(val))  # type: ignore[arg-type]
            await redis_client.delete(k)

        assert results == list(range(20))


# ─────────────────────────────────────────────────────────────────────────────
# Combined Infrastructure Health Test
# ─────────────────────────────────────────────────────────────────────────────


class TestInfrastructureHealth:
    @pytest.mark.asyncio
    async def test_both_services_reachable_simultaneously(self):
        """
        Final gate check: both Postgres and Redis must be reachable
        in the same test to confirm the full infrastructure stack is healthy.
        """
        import asyncpg
        import redis.asyncio as aioredis

        from aitester.core.config import settings

        # Postgres
        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        pg_conn = await asyncpg.connect(url)
        pg_result = await pg_conn.fetchval("SELECT 42")
        await pg_conn.close()

        # Redis
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.set("aitester:health:check", "ok", ex=5)
        redis_result = await redis_client.get("aitester:health:check")
        await redis_client.aclose()

        assert pg_result == 42
        assert redis_result == "ok"
