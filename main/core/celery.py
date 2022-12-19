import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'action_per_minute': {
        'task': 'billing.tasks.watch_payments',
        'schedule': crontab(minute='*/1'),
    },
    'action_every_day': {
        'task': 'billing.tasks.block_or_notification_user',
        'schedule': crontab(hour='12', minute='0'),
    },
}
app.autodiscover_tasks()
