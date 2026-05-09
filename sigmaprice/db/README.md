# Модуль 1: База данных

## Назначение

Модуль 1 отвечает за структуру базы данных системы SigmaPrice. Это фундамент — все остальные модули работают с данными через эту схему.

Модуль создаёт:
- 13 таблиц PostgreSQL с полями, типами, связями и индексами
- SQLAlchemy модели для работы с БД из Python
- Alembic миграции для версионирования изменений схемы
- Скрипт первичной инициализации БД

## Таблицы

| Таблица | Назначение |
|---------|------------|
| suppliers | Карточки поставщиков |
| supplier_rules | Правила-исключения для каждого поставщика |
| supplier_column_map | Маппинг колонок прайса поставщика |
| categories | Иерархия категорий каталога |
| catalog_items | Наши позиции каталога |
| supplier_items | Позиции из прайсов поставщиков |
| supplier_item_mapping | Таблица соответствий: наш код ↔ код поставщика |
| price_history | История цен (последние 3 выгрузки) |
| item_embeddings | Векторные эмбеддинги для ИИ-сопоставления |
| users | Пользователи системы |
| user_permissions | Права доступа по категориям и поставщикам |
| feedback_items | Комментарии пользователей об ошибках |
| knowledge_base | База знаний: выученные правила сопоставления |

## Файлы

- `models.py` — SQLAlchemy модели всех таблиц
- `schema.sql` — DDL-схема для прямого создания БД
- `migrations/` — Alembic миграции
- `init_db.py` — Скрипт первичной инициализации БД

## Использование

### Инициализация БД

```bash
# Запуск PostgreSQL и Redis
docker-compose up -d

# Создание таблиц
python -m sigmaprice.db.init_db

# Создание админа
python -m sigmaprice.db.init_db admin admin123
```

### Применение миграций

```bash
alembic upgrade head
```

### Запуск тестов

```bash
pytest sigmaprice/tests/test_db.py -v
```

## Зависимости

Добавлены в requirements.txt:
- sqlalchemy==2.0.23
- alembic==1.12.1
- psycopg2-binary==2.9.9
- pgvector==0.2.4
- passlib[bcrypt]==1.7.4
- pydantic-settings==2.1.0