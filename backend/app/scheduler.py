"""Планировщик загрузки факта (cron) — сервис scheduler."""
import logging
import time
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import settings
from app.infrastructure.connectors.csv_data_source import CsvDataSource
from app.infrastructure.db.models import ConstructionObject
from app.infrastructure.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_fact_load():
    db = SessionLocal()
    try:
        import_dir = Path(settings.fact_import_dir)
        files = list(import_dir.glob("fact_*.csv")) + list(import_dir.glob("fact_*.xlsx"))
        if not files:
            logger.info("No fact files to load")
            return
        objects = db.query(ConstructionObject).all()
        code_map = {o.code: o.id for o in objects}
        csv_source = CsvDataSource()
        log = csv_source.load_fact_data(db, str(files[0]), code_map)
        logger.info("Fact load: %s, records=%s", log.status, log.records_loaded)
    finally:
        db.close()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run_fact_load, "cron", hour=2, minute=0)
    logger.info("Scheduler started (daily at 02:00)")
    while True:
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            break
        time.sleep(60)
