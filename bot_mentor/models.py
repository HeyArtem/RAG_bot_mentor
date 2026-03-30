from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from pgvector.django import VectorField

# from bot_mentor.tasks import process_document Артем, не делай  circular import.
# Положи это в def save


CATEGORY_CHOICES = [("menu", "Меню"), ("bar", "Бар"), ("standards", "Стандарты")]


# -------------------------------------------------------------
#                   1. МОДЕЛИ ДАННЫХ (RAG CORE)
# -------------------------------------------------------------


class UploadedFile(models.Model):
    """
    Хранит информацию о сырых файлах, которые пользователь
    загружает в систему для последующего анализа.

    Назначение:
    - хранить путь к файлу на диске
    - сохранять оригинальное имя файла и дату загрузки
    - предоставлять связь для связанных фрагментов (Chunk)
    """

    file = models.FileField(
        upload_to="uploaded_files/",
        verbose_name="Файл",
        validators=[FileExtensionValidator(allowed_extensions=["txt", "md", "pdf"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    @property
    def file_name(self):
        return self.file.name.split("/")[-1]

    def __str__(self):
        return self.file_name

    class Meta:
        db_table = "uploaded_files"
        verbose_name = "Загруженный файл"
        verbose_name_plural = "Загруженные файлы"


class Document(models.Model):
    """
    Документ с категорией (меню / бар / стандарты).
    Связывает сырой файл с его смысловым контекстом (категорией).

    Например:
    - category = "menu"
    - title = "Меню кухни"
    - file → menu.txt

    При обновлении файла старый документ удаляем, создаём новый.
    """

    title = models.CharField(verbose_name="Название документа", max_length=255)
    category = models.CharField(
        verbose_name="Категория", max_length=20, choices=CATEGORY_CHOICES
    )
    uploaded_file = models.ForeignKey(
        UploadedFile,
        verbose_name="Исходный файл",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    version = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        # Если этот документ сохраняется как активный
        if self.is_active:
            # ⚡️ Атомарная операция: находим все активные документы
            # этой же категории и выключаем их (кроме текущего)
            Document.objects.filter(category=self.category, is_active=True).exclude(
                pk=self.pk
            ).update(is_active=False)

        # 1. Сначала сохраняем файл и запись в БД (стандартное поведение)
        super().save(*args, **kwargs)

        """
        Золотое правило Celery в Django:
        никогда не импортируй задачи (из tasks.py)
        на верхнем уровне в models.py.
        Что бы не бвыло circular import, импорт клaду сюда
        """
        from bot_mentor.tasks import process_document

        # Если это новый файл или обновление — запускаем Celery
        # transaction.on_commit гарантирует, что задача уйдет в Celery
        # ТОЛЬКО после того, как файл точно запишется на диск и в базу.
        transaction.on_commit(lambda: process_document.delay(self.pk))

    def __str__(self):
        return f" {self.title} ({self.category})"

    class Meta:
        db_table = "documents"
        verbose_name = "Документ"
        verbose_name_plural = "Документы"


class Chunk(models.Model):
    """
    Основное хранилище знаний для RAG
    Чанк = небольшой кусок текста (примерно 500–1500 символов),
    который был вырезан из документа и получил вектор через OpenAI Embeddings API.

    Используется Postgres + pgvector, чтобы искать похожие чанки
    и находить нужную информацию при вопросе стажера.

    Поля:
    - chunk_text: текст чанка
    - embedding: вектор (список чисел)
    - chunk_index: номер чанка внутри документа
    """

    document = models.ForeignKey(
        Document,
        verbose_name="Документ-источник",
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField(verbose_name="Порядковый номер чанка")

    chunk_text = models.TextField(verbose_name="Текст чанка")

    # embedding = VectorField(
    #     verbose_name="Вектор эмбеддинга",
    #     dimensions=1536,  # под OpenAI text-embedding-3-small
    # )

    # Эксперименты
    embedding = VectorField(
        verbose_name="Вектор эмбеддинга",
        dimensions=3072,  # под OpenAI text-embedding-3-large
    )

    def __str__(self):
        return f"Чанк #{self.chunk_index} из '{self.document.title}'"

    class Meta:
        db_table = "chunks"
        verbose_name = "Чанк"
        verbose_name_plural = "Чанки"


class TelegramUser(models.Model):
    ROLE_CHOICES = [
        ("trainee", "Стажер"),
        ("waiter", "Официант"),
        ("manager", "Менеджер"),
    ]
    telegram_id = models.BigIntegerField(unique=True, verbose_name="ID пользователя")
    username = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Никнейм @username"
    )
    full_name = models.CharField(max_length=255, blank=True, verbose_name="ФИО")
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="trainee", verbose_name="Роль"
    )
    is_approved = models.BooleanField(default=False, verbose_name="Доступ_подтвержден")
    # Поле для понимания, может ли этот юзер заходить в админку сайта
    is_admin = models.BooleanField(default=False, verbose_name="Права администратора")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации"
    )

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    class Meta:
        db_table = "bot_mentor_telegramuser"
        verbose_name = "Пользователь бота"
        verbose_name_plural = "Пользователи бота"


# -------------------------------------------------------------
#                 2. МОДЕЛИ ЛОГИРОВАНИЯ И АНАЛИТИКИ
# -------------------------------------------------------------


class Question(models.Model):
    """
    Лог вопросов, заданных пользователем (стажером) системе.
    Используется для аналитики и просмотра истории.
    """

    user_id = models.BigIntegerField(  # BigInt для Telegram ID
        null=True, blank=True, verbose_name="ID пользователя в Telegram"
    )
    question_text = models.TextField(verbose_name="Текст вопроса")
    answer_text = models.TextField(verbose_name="Ответ системы", null=True, blank=True)
    # embedding = VectorField(
    #     dimensions=1536, verbose_name="Вектор вопроса", null=True, blank=True
    # )

    # Эксперим
    embedding = VectorField(
        dimensions=3072, verbose_name="Вектор вопроса", null=True, blank=True
    )

    document_category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        null=True,
        blank=True,
        verbose_name="Категория документа",
    )
    score = models.FloatField(
        null=True, blank=True, verbose_name="Оценка релевантности"
    )
    session_id = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="ID сессии"
    )
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    def __str__(self):
        return f"Вопрос от {self.user_id}: {self.question_text[:30]}..."

    class Meta:
        db_table = "questions"
        verbose_name = "Лог вопроса"
        verbose_name_plural = "Логи вопросов"


class UserProgress(models.Model):
    """
    Отслеживает прогресс пользователя по категориям.
    """

    user_id = models.IntegerField(verbose_name="ID пользователя в Telegram")
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, verbose_name="Категория"
    )
    completed = models.BooleanField(default=False, verbose_name="Завершено")
    score = models.IntegerField(null=True, blank=True, verbose_name="Лучший результат")
    last_attempt = models.DateTimeField(auto_now=True, verbose_name="Последняя попытка")
    attempts_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество попыток"
    )

    class Meta:
        db_table = "user_progress"
        unique_together = ["user_id", "category"]
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"

    def __str__(self):
        # return f"User {self.user_id} - {self.category}: {'Сдан' if self.completed else 'In progress'}"

        # get_category_display() - джанго метод, показывает "Меню" вместо "menu"
        return f"{self.user_id} - {self.get_category_display()}: {'Сдан' if self.completed else 'В процессе'}"


class TestResult(models.Model):
    """
    Детализация результатов прохождения теста пользователем.
    """

    user_id = models.IntegerField(verbose_name="ID пользователя")
    category = models.CharField(max_length=20, verbose_name="Категория теста")
    total_questions = models.PositiveIntegerField(verbose_name="Всего вопросов")
    correct_answers = models.PositiveIntegerField(verbose_name="Верных ответов")
    score = models.FloatField(verbose_name="Процент верных ответов")
    passed = models.BooleanField(verbose_name="Тест сдан")
    completed_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата завершения"
    )

    class Meta:
        db_table = "test_results"  # 👈 Добавлено
        verbose_name = "Результат теста"
        verbose_name_plural = "Результаты тестов"

    def __str__(self):
        return f"Test: {self.user_id} - {self.category} - {self.score}%"
