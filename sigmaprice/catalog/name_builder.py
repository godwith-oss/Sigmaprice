"""Normalized name building for catalog items"""
import re
from sigmaprice.core.types import RawItem
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)

CATEGORY_VIDEO_CARD = "Видеокарты"
CATEGORY_MOTHERBOARD = "Материнские платы"
CATEGORY_PROCESSOR = "Процессоры"
CATEGORY_SSD = "SSD"
CATEGORY_RAM = "Оперативная память"
CATEGORY_PSU = "Блоки питания"


def build_name(item: RawItem, category_name: str = "") -> str:
    """
    Build a normalized catalog name from RawItem.

    Format depends on category:
    - Video cards: "Видеокарта {manufacturer} {model} {memory}Gb"
    - Motherboards: "Материнская плата {manufacturer} {model}, {socket}"
    - Processors: "Процессор {manufacturer} {model}, {socket}"
    - SSD: "SSD {manufacturer} {model} {capacity}"
    - Other: "{manufacturer} {name}" (normalized)

    Requirements:
    - Human readable
    - Contains key characteristics
    - Manufacturer casing preserved
    - No extra spaces or symbols
    """
    name = item.name.strip()
    name = re.sub(r'\s+', ' ', name)
    manufacturer = (item.manufacturer or "").strip()

    if CATEGORY_VIDEO_CARD in category_name:
        return _build_video_card_name(manufacturer, name, item.description)

    if CATEGORY_MOTHERBOARD in category_name:
        return _build_motherboard_name(manufacturer, name, item.description)

    if CATEGORY_PROCESSOR in category_name:
        return _build_processor_name(manufacturer, name, item.description)

    if CATEGORY_SSD in category_name:
        return _build_ssd_name(manufacturer, name, item.description)

    if CATEGORY_RAM in category_name:
        return _build_ram_name(manufacturer, name, item.description)

    if CATEGORY_PSU in category_name:
        return _build_psu_name(manufacturer, name, item.description)

    return _build_generic_name(manufacturer, name)


def _build_video_card_name(manufacturer: str, name: str, description: str) -> str:
    """Build video card name: Видеокарта {manufacturer} {model}"""
    memory_match = re.search(r'(\d+)\s*G[bB]', name)
    memory = f" {memory_match.group(1)}Gb" if memory_match else ""

    if manufacturer and name.startswith(manufacturer):
        return f"Видеокарта {name}{memory}"
    if manufacturer:
        return f"Видеокарта {manufacturer} {name}{memory}"
    return f"Видеокарта {name}{memory}"


def _build_motherboard_name(manufacturer: str, name: str, description: str) -> str:
    """Build motherboard name: Материнская плата {manufacturer} {model}, {socket}"""
    socket = _extract_socket(name, description)

    if manufacturer and name.startswith(manufacturer):
        base = f"Материнская плата {name}"
    elif manufacturer:
        base = f"Материнская плата {manufacturer} {name}"
    else:
        base = f"Материнская плата {name}"

    if socket:
        return f"{base}, {socket}"
    return base


def _build_processor_name(manufacturer: str, name: str, description: str) -> str:
    """Build processor name: Процессор {manufacturer} {model}, {socket}"""
    socket = _extract_socket(name, description)

    if manufacturer and name.startswith(manufacturer):
        base = f"Процессор {name}"
    elif manufacturer:
        base = f"Процессор {manufacturer} {name}"
    else:
        base = f"Процессор {name}"

    if socket:
        return f"{base}, {socket}"
    return base


def _build_ssd_name(manufacturer: str, name: str, description: str) -> str:
    """Build SSD name: SSD {manufacturer} {model} {capacity}"""
    capacity_match = re.search(
        r'(\d+)\s*(T[Bb]|G[Bb])', name + " " + (description or "")
    )

    if manufacturer and name.startswith(manufacturer):
        base = f"SSD {name}"
    elif manufacturer:
        base = f"SSD {manufacturer} {name}"
    else:
        base = f"SSD {name}"

    if capacity_match:
        return f"{base} {capacity_match.group(0)}"
    return base


def _build_ram_name(manufacturer: str, name: str, description: str) -> str:
    """Build RAM name: {manufacturer} {model} {capacity}"""
    if manufacturer and name.startswith(manufacturer):
        return name
    if manufacturer:
        return f"{manufacturer} {name}"
    return name


def _build_psu_name(manufacturer: str, name: str, description: str) -> str:
    """Build PSU name: {manufacturer} {model} {wattage}W"""
    if manufacturer and name.startswith(manufacturer):
        return name
    if manufacturer:
        return f"{manufacturer} {name}"
    return name


def _build_generic_name(manufacturer: str, name: str) -> str:
    """Build generic name: {manufacturer} {name}"""
    if manufacturer and not name.lower().startswith(manufacturer.lower()):
        return f"{manufacturer} {name}"
    return name


def _extract_socket(name: str, description: str = "") -> str:
    """Extract socket type from name or description."""
    sockets = [
        "LGA1851", "LGA1700", "LGA1200", "LGA1151", "LGA1150",
        "AM5", "AM4", "AM3+", "sTRX4", "sWRX8",
    ]
    text = f"{name} {(description or '')}"
    text_upper = text.upper()

    for socket in sockets:
        if socket.upper() in text_upper:
            return socket

    am_match = re.search(r'AM\d(\+)?', text, re.IGNORECASE)
    if am_match:
        return am_match.group(0)

    lga_match = re.search(r'LGA\d{3,4}', text, re.IGNORECASE)
    if lga_match:
        return lga_match.group(0)

    return ""
