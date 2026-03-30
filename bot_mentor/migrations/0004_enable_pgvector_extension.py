from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    dependencies = [
        ("bot_mentor", "0003_alter_chunk_embedding_alter_question_embedding"),
    ]

    operations = [
        VectorExtension(),
    ]
