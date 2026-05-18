"""Knowledge base module — AI hints, exclusions, suffix & synonym dictionaries"""
from sigmaprice.knowledge.manager import (
    add_rule,
    get_rules,
    get_patterns_by_type,
    is_excluded_by_kb,
    get_suffixes,
    get_synonyms,
    seed_default_rules,
    delete_rule,
)

__all__ = [
    "add_rule",
    "get_rules",
    "get_patterns_by_type",
    "is_excluded_by_kb",
    "get_suffixes",
    "get_synonyms",
    "seed_default_rules",
    "delete_rule",
]
