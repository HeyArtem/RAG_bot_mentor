from django.contrib import admin

from .models import Chunk, Document, Question, TestResult, UploadedFile, UserProgress

# from .tasks import process_document


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "file_name",
        "uploaded_at",
    )
    search_fields = ("file",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "uploaded_file", "created_at")
    list_filter = ("category",)  # Фильтр справа (Меню/Бар/Стандарты)
    search_fields = ("title",)


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "chunk_index",
        "short_text",
    )  # short_text - наш кастомный метод ниже
    list_filter = ("document__category", "document")  # Фильтр по категории документа
    search_fields = ("chunk_text",)

    def short_text(self, obj):
        return obj.chunk_text[:50] + "..."

    short_text.short_description = "Текст чанка"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "question_text",
        "document_category",
        "score",
        "created_at",
    )
    list_filter = ("document_category", "created_at")
    search_fields = ("question_text", "user_id")
    readonly_fields = ("created_at",)


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "category",
        "completed",
        "score",
        "attempts_count",
        "last_attempt",
    )
    list_filter = ("category", "completed")
    search_fields = ("user_id",)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "category",
        "score",
        "passed",
        "completed_at",
        "total_questions",
        "correct_answers",
    )
    list_filter = ("passed", "category")
