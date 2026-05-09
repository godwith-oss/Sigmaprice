# Модуль 2: Управление поставщиками

## Назначение

Модуль 2 отвечает за работу с поставщиками: создание карточек, настройка правил расчёта цен, правил-исключений для фильтрации товаров и маппинга колонок прайсов.

## Использование

### Создание поставщика

```python
from sigmaprice.suppliers import create_supplier

supplier = create_supplier(
    name="TechSupply",
    country="Russia",
    currency="USD",
    vat_included=False,
    price_formula="price * usd_rate * 1.2"
)
```

### Управление правилами

```python
from sigmaprice.suppliers import add_rule, get_rules, should_exclude
from sigmaprice.core.types import RawItem, AvailabilityStatus

# Добавить правило исключения
rule = add_rule(
    supplier_id=1,
    rule_type="exclude_keyword",
    rule_value="demo"
)

# Проверить товар на исключение
item = RawItem(
    supplier_id=1,
    supplier_code="SKU001",
    name="Demo NVIDIA RTX 5080",
    description=None,
    price=1000,
    currency="USD",
    availability=AvailabilityStatus.IN_STOCK,
    quantity=10,
    warranty_months=36,
    article=None,
    ean=None,
    manufacturer="NVIDIA",
    delivery_type=None
)

if should_exclude(1, item):
    print("Товар исключён")
```

### Расчёт цены

```python
from sigmaprice.suppliers import calculate_price
from decimal import Decimal

price = calculate_price(
    supplier_id=1,
    price_original=Decimal("100.00"),
    exchange_rates={"usd_rate": 95.5}
)
```

### Маппинг колонок

```python
from sigmaprice.suppliers import set_column_mapping, get_column_mapping

# Сохранить маппинг
set_column_mapping(1, {
    'code': 'Код',
    'name': 'Наименование',
    'price': 'Цена',
    'availability': 'Наличие',
    'article': 'Артикул',
})

# Получить маппинг
mapping = get_column_mapping(1)
print(mapping)
```

## Типы правил

| Тип | Пример значения | Описание |
|-----|----------------|----------|
| `exclude_sheet` | `'Б/У'` | Исключить лист Excel с именем |
| `exclude_category` | `'Расходники'` | Исключить категорию |
| `exclude_keyword` | `'demo'` | Исключить если в названии есть слово |
| `price_range` | `'min:100,max:50000'` | Фильтр по диапазону цен |

## Формулы цен

Примеры формул:
- `'price'` — без изменений
- `'price * 1.2'` — накрутка 20%
- `'price * usd_rate'` — конвертация по курсу
- `'price * usd_rate * 1.2'` — конвертация + НДС

Доступные переменные: `price`, `usd_rate`, `eur_rate`, `rub_rate`, `vat`, `nds`

## Файлы модуля

- `manager.py` — CRUD операции с поставщиками
- `rules.py` — Правила-исключения
- `pricing.py` — Расчёт цен по формуле
- `column_mapping.py` — Маппинг колонок прайса