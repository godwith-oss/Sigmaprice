# Модуль 4: Сопоставление товаров

## Назначение

Модуль сопоставляет товары из прайсов поставщиков с каталогом. Поддерживает 5 уровней сопоставления.

## Алгоритм сопоставления

| Уровень | Метод | Описание |
|---------|-------|-----------|
| 1 | Правила | Нормализация, синонимы, словарь суффиксов |
| 2 | Атрибуты | Точное совпадение по артикулу, EAN |
| 3 | ИИ локально | Семантическое сравнение через эмбеддинги |
| 4 | ИИ + интернет | Веб-поиск (Claude, OpenAI, Ollama) |
| 5 | Очередь | На проверку админу |

## Использование

```python
from sigmaprice.matcher import match_item
from sigmaprice.core.types import RawItem, AvailabilityStatus

item = RawItem(
    supplier_id=1,
    supplier_code="RTX5080-001",
    name="Видеокарта NVIDIA GeForce RTX 5080",
    description=None,
    price=Decimal("1500"),
    currency="USD",
    availability=AvailabilityStatus.IN_STOCK,
    quantity=10,
    warranty_months=36,
    article="RTX5080",
    ean=None,
    manufacturer="NVIDIA",
    delivery_type="Retail"
)

result = match_item(item, supplier_id=1)
print(f"Matched: {result.catalog_item_id}, confidence: {result.confidence}")
```

## Конфигурация

Создайте `.env` файл:

```bash
# Matcher configuration
MATCHER_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
MATCHER_EMBEDDING_THRESHOLD=0.85
MATCHER_WEB_PROVIDER= # claude / openai / ollama / пусто

# API keys
CLAUDE_API_KEY=
OPENAI_API_KEY=

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Переключение моделей эмбеддингов

```python
from sigmaprice.matcher.config import MatcherConfig
from sigmaprice.matcher.matcher import match_item

config = MatcherConfig(
    embedding_model="paraphrase-multilingual-mpnet-base-v2",
    embedding_threshold=0.9
)
result = match_item(item, supplier_id, config)
```

## Пересчёт эмбеддингов

При смене модели эмбеддингов нужно пересчитать все векторы:

```bash
python -m sigmaprice.matcher.rebuild_embeddings
```

## Поддерживаемые модели

| Модель | Размерность | Языки |
|--------|-------------|-------|
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | 50+ |
| paraphrase-multilingual-mpnet-base-v2 | 768 | 50+ |
| all-MiniLM-L6-v2 | 384 | EN |
| intfloat/multilingual-e5-large | 1024 | 100+ |

## Файлы модуля

- `matcher.py` — основная логика сопоставления
- `config.py` — конфигурация
- `providers.py` — абстрактные классы
- `embedding_provider.py` — sentence-transformers провайдер
- `web_providers.py` — Claude, OpenAI, Ollama провайдеры
- `factory.py` — фабрика провайдеров
- `rebuild_embeddings.py` — пересчёт эмбеддингов