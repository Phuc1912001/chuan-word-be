"""Celery app cho xử lý phân tích nền.

Chạy worker: celery -A app.worker.celery_app:celery_app worker --loglevel=info
(Windows local: thêm --pool=solo)
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "chuanword",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
)

# đăng ký task
from app.worker import tasks  # noqa: E402,F401
