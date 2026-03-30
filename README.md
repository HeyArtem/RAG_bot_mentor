В работе

Что занести

# TODO
-Сохранение в БД (Bulk Create)
# Собираем объекты в список, чтобы сохранить одним SQL-запросом
        chunks_to_create = []
        for i, (chunk_content, vector) in enumerate(zip(chunks_text, vectors)):
            chunks_to_create.append(
                Chunk(
                    document=doc,
                    chunk_index=i,
                    chunk_text=chunk_content,
                    embedding=vector
                )
            )

        Chunk.objects.bulk_create(chunks_to_create)
-настройка, которая отключает внутреннюю проверку токенов в библиотеке langchain-openai.
		Что делает эта проверка:
		Прежде чем отправить текст в OpenAI, библиотека хочет посчитать, не превысил ли ты лимит токенов модели (обычно 8192 токена для эмбеддингов).
check_embedding_ctx_length=False

embedding_model = OpenAIEmbeddings(
    model=settings.AI_EMBEDDING_MODEL,  # 'text-embedding-3-small'
    openai_api_key=settings.AI_EMBEDDING_KEY,
    openai_api_base=settings.OPENAI_API_BASE,
    check_embedding_ctx_length=False  # Отключаем лишние проверки токенов у langchain-openai
)


-separators=["\n\n", "\n", " ", ""]

text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )

"Менеджер должен помнить, что [ТУТ РАЗРЕЗ] зарплата выдается 5го числа."
		Специальный объект RecursiveCharacterTextSplitter пытается резать умнее. Он использует список разделителей (separators):
		-Он сначала пытается резать по двойному переносу строки (\n\n) — это обычно конец абзаца.
		-Если не получилось (чанк все равно больше 1000), он пытается резать по одинарному переносу (\n) — конец строки.
		-Если не получилось, режем по пробелу ( ) — конец слова.
		-Если и это не помогло, режем по символу ( ).
		Главная идея: Он использует разделители в порядке убывания "смысловой важности". Это гарантирует, что ты не разорвешь слово, если можешь разорвать предложение, и не разорвешь предложение, если можешь разорвать абзац.

# 3. Нарезка на Чанки (Chunking)
        # 1000 символов размер, 100 символов перехлест (чтобы не рвать предложения)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )



# TODO
В Django для этого есть специальный инструмент — Management Commands (команды управления).
management/commands — это «соглашение». Django сам сканирует эти папки. Когда ты пишешь python manage.py ..., Django сначала подгружает всё своё «тело», а потом вставляет твой скрипт как «палец в перчатку».

Про stdout.write и стили (SUCCESS, ERROR)
self.stdout.write: Да, это аналог print. Но в профессиональных инструментах print считается дурным тоном. stdout.write работает через стандартные потоки вывода.

Стили: Это именно уровни визуализации. В терминале SUCCESS подсветит текст зеленым, ERROR — красным, WARNING — желтым. Это помогает глазу сразу видеть, где проблема, а где успех.



Blue-Green Deployment
Blue-green deployment (сине-зелёное развёртывание) — это стратегия непрерывной поставки (CI/CD), обеспечивающая обновление приложений с нулевым простоем (zero-downtime) и мгновенным откатом. Она использует две идентичные изолированные среды — «синюю» (текущая) и «зелёную» (новая). Пока работает одна, вторая обновляется и тестируется, затем трафик переключается на неё.
Как это работает:
Blue (Active): Версия 1.0 работает для пользователей.
Green (Stage): Версия 2.0 разворачивается в параллельной среде.
Переключение: Пройдя тесты, трафик переключается на версию 2.0.
Смена ролей: Теперь Green становится активной, а старая Blue ожидает до следующего релиза.
Эта стратегия требует двойного объёма ресурсов, но минимизирует риски.


Типы запросов
	Тип 👽 Type 1 (простой):
		"вишня", "вшн", "ДЕГУСТАЦИОННЫЙ", "краб"
	♻️ Этот тип запроса (осоновной) мы обработаем не обращаясь к LLM. Ищем Прямое совпадение в тексте запроса и текстах чанков.
	Методы:
		ºKeyword search,
		ºLexical search,
		ºFull-text search,
		ºTrigram similarity.

	Тип 👽 Type 2 (сложный):
		"ягды", "ягоды" "фрукты", "мясо"
	♻️ Если приходит этот тип запроса мы трансформируем user_text в вектор. Подбираем ближайшие вектора из нашей БД и вместе с промптом отправляем в LLM.
	Методы:
		ºSemantic retrieval,
		ºVector search,
		ºApproximate Nearest Neighbors (ANN),
		ºRAG (Retrieval Augmented Generation)


	Пайплайн
	♻️ START
	🧬user_text: str → 🧬Telegram → 🧬Aiogram handler → 🧬user_text.lower().strip() → 🧬-👽 Type 1(простой) [SELECT * FROM chunk WHERE chunk_text ILIKE '%краб%' ORDER BY document, chunk_index;❗️хочу протестить❗️. pg_trgm — это Postgres extension для борьбы с опечатками.] → 🧬 Выдаем ответ пользователю <=> Смена типа поиска на -👽 Type 2.fallback в Type 2.


	→ 🧬если 👽 Type 2 (Semantic / RAG) → 🧬Преващаем user_text в вектор, берем похожие вектора в базе и вместе в промптом отправляем в LLM (У меня сейчас так.). Threshold / Re-ranking / фильтрация❓ (что это?) → 🧬LLM генерирует ответ, не переписывая текст, а интерпретируя / комбинируя факты (Здесь LLM незаменим, т.к. нужен reasoning.❓Что такое reasoning).
