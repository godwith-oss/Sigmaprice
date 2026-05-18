"""Category management and item categorization"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sigmaprice.db.models import Category, CatalogItem
from sigmaprice.core.types import RawItem
from sigmaprice.core.exceptions import ValidationError
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

CATEGORY_KEYWORDS = {
    "Видеокарты": [
        "видеокарта", "geforce", "radeon", "rtx", "gtx", "rx",
        "nvidia", "amd radeon", "graphics card",
    ],
    "Материнские платы": [
        "материнская плата", "motherboard", "матплата",
    ],
    "Процессоры": [
        "процессор", "cpu", "ryzen", "intel core", "core i",
        "core ultra", "threadripper", "epyc", "xeon",
    ],
    "SSD": [
        "ssd", "nvme", "sata ssd", "твердотельный",
    ],
    "Оперативная память": [
        "оперативная память", "dimm", "sodimm", "ddr4", "ddr5",
        "ram", "память",
    ],
    "Блоки питания": [
        "блок питания", "psu", "power supply", "бп",
    ],
    "Корпуса": [
        "корпус", "case", "midi tower", "full tower",
    ],
    "Кулеры и СО": [
        "кулер", "cooler", "водяное", "система охлаждения",
        "вентилятор", "fan", "радиатор",
    ],
    "Мониторы": [
        "монитор", "monitor",
    ],
    "Клавиатуры": [
        "клавиатура", "keyboard",
    ],
    "Мыши": [
        "мышь", "мышка", "mouse",
    ],
    "Ноутбуки": [
        "ноутбук", "laptop", "notebook",
    ],
}

DEFAULT_CATEGORY = "Прочее"


def create_category(
    name: str,
    parent_id: Optional[int] = None,
    sort_field: str = "price",
    session: Optional[Session] = None,
) -> Category:
    """Create a new category."""
    name = name.strip()
    if not name:
        raise ValidationError("Category name cannot be empty")

    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    category = Category(
        name=name,
        parent_id=parent_id,
        sort_field=sort_field,
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    logger.info(f"Created category: {category.name} (ID: {category.id})")
    return category


def get_category(category_id: int, session: Optional[Session] = None) -> Optional[Category]:
    """Get category by ID."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(Category).filter(Category.id == category_id).first()


def get_category_by_name(name: str, session: Optional[Session] = None) -> Optional[Category]:
    """Get category by name (exact match, case-insensitive)."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    return session.query(Category).filter(
        Category.name.ilike(name.strip())
    ).first()


def get_or_create_default_category(session: Session) -> Category:
    """Get or create the default 'Прочее' category."""
    cat = get_category_by_name(DEFAULT_CATEGORY, session)
    if cat is None:
        cat = create_category(DEFAULT_CATEGORY, parent_id=None, session=session)
    return cat


def get_category_tree(session: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Return category tree as nested dict list.

    Format:
    [
        {
            'id': 1,
            'name': 'Видеокарты',
            'parent_id': None,
            'children': [
                {'id': 2, 'name': 'NVIDIA', 'parent_id': 1, 'children': []},
            ]
        }
    ]
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    categories = session.query(Category).order_by(Category.name).all()

    category_dict: Dict[int, Dict[str, Any]] = {}
    for cat in categories:
        category_dict[cat.id] = {
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "sort_field": cat.sort_field,
            "children": [],
        }

    roots: List[Dict[str, Any]] = []
    for cat in categories:
        node = category_dict[cat.id]
        if cat.parent_id and cat.parent_id in category_dict:
            category_dict[cat.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def update_category(
    category_id: int,
    session: Optional[Session] = None,
    **kwargs,
) -> Category:
    """Update category fields."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    category = session.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise ValidationError(f"Category with ID {category_id} not found")

    allowed = ["name", "parent_id", "sort_field"]
    for key, value in kwargs.items():
        if key in allowed and value is not None:
            setattr(category, key, value.strip() if isinstance(value, str) else value)

    session.commit()
    session.refresh(category)
    logger.info(f"Updated category: {category.name} (ID: {category.id})")
    return category


def delete_category(
    category_id: int,
    reassign_category_id: Optional[int] = None,
    session: Optional[Session] = None,
) -> bool:
    """
    Delete a category.

    If the category contains items:
    - If reassign_category_id is provided, move items there
    - Otherwise, move items to the default category
    - If no default category exists, raise an error

    Returns True if deleted, False if not found.
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    category = session.query(Category).filter(Category.id == category_id).first()
    if not category:
        return False

    items = session.query(CatalogItem).filter(
        CatalogItem.category_id == category_id
    ).all()

    if items:
        if reassign_category_id:
            target = session.query(Category).filter(
                Category.id == reassign_category_id
            ).first()
            if not target:
                raise ValidationError(
                    f"Target category {reassign_category_id} not found"
                )
        else:
            target = get_or_create_default_category(session)

        for item in items:
            item.category_id = target.id

        logger.info(
            f"Reassigned {len(items)} items from category "
            f"'{category.name}' to '{target.name}'"
        )

    session.delete(category)
    session.commit()

    logger.info(f"Deleted category: {category.name} (ID: {category_id})")
    return True


def list_categories(
    parent_id: Optional[int] = None,
    session: Optional[Session] = None,
) -> List[Category]:
    """List categories, optionally filtered by parent."""
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    query = session.query(Category)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    else:
        query = query.filter(Category.parent_id.is_(None))

    return query.order_by(Category.name).all()


def determine_category(item: RawItem, session: Optional[Session] = None) -> int:
    """
    Determine category for a raw item.

    Algorithm:
    1. Check keywords in name + description
    2. Fallback to default category 'Прочее'

    Returns category_id.
    AI-based classification is handled by Module 4
    and passed through match_result.
    """
    from sigmaprice.core.database import get_session
    if session is None:
        session = get_session()

    text = (
        f"{item.name.lower()} "
        f"{(item.description or '').lower()} "
        f"{(item.manufacturer or '').lower()}"
    )

    for category_name, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                cat = get_category_by_name(category_name, session)
                if cat:
                    logger.debug(
                        f"Keyword match: '{keyword}' -> category '{category_name}'"
                    )
                    return cat.id

                cat = create_category(category_name, session=session)
                return cat.id

    default = get_or_create_default_category(session)
    logger.debug(f"No keyword match, fallback to '{DEFAULT_CATEGORY}'")
    return default.id


def ensure_default_categories(session: Session) -> List[int]:
    """
    Ensure all predefined categories exist in DB.
    Called once at startup to initialize category structure.
    Returns list of all category IDs.
    """
    ids = []
    for name in list(CATEGORY_KEYWORDS.keys()) + [DEFAULT_CATEGORY]:
        cat = get_category_by_name(name, session)
        if cat is None:
            cat = create_category(name, session=session)
        ids.append(cat.id)
    logger.info(f"Ensured {len(ids)} default categories exist")
    return ids
