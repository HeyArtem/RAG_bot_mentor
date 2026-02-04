# Это нужно, чтобы celery всегда запускался, когда Django стартует
from .celery import app as celery_app

# Это позволяет Django загрузить Celery при старте
__all__ = ("celery_app",)
