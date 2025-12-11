from django.core.validators import FileExtensionValidator
from django.db import models
from pgvector.django import VectorField

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

    embedding = VectorField(
        verbose_name="Вектор эмбеддинга",
        dimensions=1536,  # под OpenAI text-embedding-3-small
    )

    def __str__(self):
        return f"Чанк #{self.chunk_index} из '{self.document.title}'"

    class Meta:
        db_table = "chunks"
        verbose_name = "Чанк"
        verbose_name_plural = "Чанки"


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
    embedding = VectorField(
        dimensions=1536, verbose_name="Вектор вопроса", null=True, blank=True
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
