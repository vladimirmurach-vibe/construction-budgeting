from apscheduler.schedulers.background import BackgroundScheduler


def create_scheduler(trigger_callback=None) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    if trigger_callback is not None:
        scheduler.add_job(trigger_callback, "cron", hour=2, minute=0, id="fact_loading", replace_existing=True)
    return scheduler
