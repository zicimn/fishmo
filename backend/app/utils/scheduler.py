from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import AsyncSessionLocal
from .counter import ViewCounter

scheduler = AsyncIOScheduler()


async def sync_job():
    """定时任务：把 Redis 中累积的文章浏览量增量批量回写数据库。"""
    async with AsyncSessionLocal() as session:
        await ViewCounter.sync_to_db(session)


def start_scheduler():
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(minutes=10),  # 每 10 分钟执行一次
        id="sync_views",
        replace_existing=True,
    )
    scheduler.start()


def shutdown_scheduler():
    # 防御：调度器可能从未被启动（start_scheduler 容错时），避免对未运行的调度器调用 shutdown 报错。
    if scheduler.running:
        scheduler.shutdown(wait=False)
