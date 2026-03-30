from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Chunk,
    Document,
    Question,
    TelegramUser,
    TestResult,
    UploadedFile,
    UserProgress,
)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    # ⚡️ Список полей, которые будут видны в таблице
    list_display = (
        "telegram_id",
        "username",
        "full_name",
        "role",
        "is_approved",
        "is_admin",
        "created_at",
    )
    # ⚡️ Фильтры справа
    list_filter = ("role", "is_approved", "is_admin")
    # ⚡️ Поиск по имени и ID
    search_fields = ("full_name", "telegram_id", "username")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "uploaded_file",
        "is_active",
        "created_at",
        "version",
    )
    list_filter = ("category", "is_active")
    search_fields = ("title",)
    readonly_fields = ("created_at", "version")


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "file_name",
        "file_link",
        "uploaded_at",
    )
    search_fields = ("file",)

    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Открыть файл</a>', obj.file.url
            )
        return "Нет файла"

    file_link.short_description = "Ссылка"


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
