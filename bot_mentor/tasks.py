from celery import shared_task

from bot_mentor.services.embedding_service import (
    process_document as service_process_document,
)


@shared_task
def process_document(document_id):
    """
    Асинхронная обертка-декоратор для запуска обработки документа.
    @shared_task говорит Celery: «это задача, которую можно положить в очередь».
    Мы вызываем его в models.py через метод .delay().
    Обычный вызов:
        process_document(id) — Django будет ждать, пока всё нарежется (админка зависнет).

    Вызов Celery:
        process_document.delay(id) — Django просто кидает записку в Redis
        и говорит пользователю: «Всё ок, сохранил!», а Celery подхватывает записку и начинает работу в фоне.
    """
    service_process_document(document_id)
