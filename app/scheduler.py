"""6시간마다 데이터를 자동 수집하는 백그라운드 스케줄러."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .collector import collect

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _job():
    logger.info("정기 데이터 수집 시작")
    try:
        collect()
    except Exception:
        logger.exception("정기 수집 실패")


def start_scheduler():
    global _scheduler
    if _scheduler:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(_job, "interval", hours=6, id="collect", next_run_time=None)
    _scheduler.start()
    logger.info("스케줄러 시작 (6시간 간격)")


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
