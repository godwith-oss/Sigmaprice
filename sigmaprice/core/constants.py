"""Common constants"""
from typing import Final

RETAIL_ALIASES: Final[list[str]] = ["retail", "rtl", "ret", "box"]
OEM_ALIASES: Final[list[str]] = ["oem"]

AVAILABILITY_PRIORITY: dict[str, int] = {
    "in_stock": 1,
    "reserved": 2,
    "on_order": 3,
    "in_transit": 4,
    "unavailable": 5,
}

MAX_CODE_VALUE: Final[int] = 99999999
MIN_CODE_VALUE: Final[int] = 10000000

DEFAULT_PRICE_HISTORY_COUNT: Final[int] = 3

EMBEDDING_DIMENSION: Final[int] = 384