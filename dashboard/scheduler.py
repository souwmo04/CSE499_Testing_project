from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

def run_add_random_day():
    print("Running add_random_day command...")
    call_command("add_random_day")

def start():
    scheduler = BackgroundScheduler()
    
    # Run every 1 minute for testing
    scheduler.add_job(
        run_add_random_day,
        trigger='interval',
        minutes=1,
        id='test_update',
        replace_existing=True
    )

    scheduler.start()
    print("APScheduler started for Dashboard app...")
