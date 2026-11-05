from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import AsyncSessionLocal
from utils.counter import ArticleViewCounter, ViewCounter

scheduler = AsyncIOScheduler()


async def sync_job() -> None:
    async with AsyncSessionLocal() as session:
        await ViewCounter.sync_to_db(session)
        await ArticleViewCounter.sync_to_db(session)


def start_scheduler() -> None:
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(minutes=10),
        id="sync_views",
        replace_existing=True,
    )
    scheduler.start()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)