"""Database migration helper."""

import asyncio

from app.db.session import Base, engine


async def migrate() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
