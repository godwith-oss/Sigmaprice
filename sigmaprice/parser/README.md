# Модуль 3: Парсинг прайсов

## Назначение

Модуль 3 отвечает за загрузку и обработку прайс-листов поставщиков. Поддерживает форматы Excel (xlsx/xls) и CSV.

## Использование

### Основное использование

```python
from pathlib import Path
from sigmaprice.parser import load_price
from sigmaprice.suppliers import create_supplier, set_column_mapping

# Создаём поставщика
supplier = create_supplier(
    name="TechSupply",
    country="Russia",
    currency="USD",
    vat_included=False,
    price_formula="price * usd_rate * 1.2"
)

# Настраиваем маппинг колонок
set_column_mapping(supplier.id, {
    'code': 'Код',
    'name': 'Наименование',
    'price': 'Цена',
    'availability': 'Наличие',
    'article': 'Артикул',
    'manufacturer': 'Производитель',
})

# Загружаем прайс
stats = load_price(supplier.id, Path("price.xlsx"))
print(stats)
# {'created': 10, 'updated': 50, 'skipped': 5, 'errors': 0}
```

### Ручной парсинг

```python
from sigmaprice.parser import parse_price_file
from pathlib import Path

items = parse_price_file(supplier_id=1, file_path=Path("price.xlsx"))
print(f"Parsed {len(items)} items")
```

### Автоопределение колонок

```python
from sigmaprice.parser import auto_detect_mapping

headers = ['Код товара', 'Наименование', 'Цена', 'Наличие', 'Артикул']
mapping = auto_detect_mapping(headers)
print(mapping)
# {'name': 'Наименование', 'price': 'Цена', ...}
```

## Форматы файлов

- **Excel**: xlsx, xls — обрабатывает все вкладки
- **CSV**: с автоопределением разделителя и кодировки

## Алгоритм обработки

1. Читает файл (все листы Excel)
2. Применяет правила-исключения поставщика
3. Ищет код в таблице соответствий
   - Найден → обновляет цену и наличие
   - Не найден → создаёт новую позицию

## Файлы модуля

- `parser.py` — основной парсер
- `loader.py` — загрузка в базу данных
- `excel_reader.py` — чтение Excel
- `csv_reader.py` — чтение CSV
- `column_mapper.py` — маппинг колонок