import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taste_matchmaker.settings")

app = Celery("taste_matchmaker")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
