"""Tests for knowledge base module"""
import pytest
from unittest.mock import MagicMock, patch
from sigmaprice.knowledge import (
    add_rule,
    get_rules,
    get_patterns_by_type,
    get_suffixes,
    get_synonyms,
    is_excluded_by_kb,
    seed_default_rules,
    delete_rule,
)
from sigmaprice.db.models import KnowledgeBase, KnowledgeBaseRuleType


class TestKnowledgeBase:
    """Test knowledge base CRUD operations."""

    @patch('sigmaprice.core.database.get_session')
    def test_add_rule(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule = MagicMock()
        rule.rule_type = KnowledgeBaseRuleType.EXCLUSION
        rule.pattern = "поврежденная упаковка"
        rule.resolution = "exclude"
        session.add.return_value = None
        session.commit.return_value = None

        with patch('sigmaprice.knowledge.manager.KnowledgeBase', return_value=rule):
            result = add_rule(
                rule_type=KnowledgeBaseRuleType.EXCLUSION,
                pattern="поврежденная упаковка",
                resolution="exclude",
                session=session,
            )

        assert result.pattern == "поврежденная упаковка"
        assert session.add.called
        assert session.commit.called

    @patch('sigmaprice.core.database.get_session')
    def test_get_rules_returns_patterns(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule1 = MagicMock()
        rule1.pattern = "pattern1"
        rule2 = MagicMock()
        rule2.pattern = "pattern2"

        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            rule1, rule2
        ]

        rules = get_rules(KnowledgeBaseRuleType.EXCLUSION, session=session)
        assert len(rules) == 2

    @patch('sigmaprice.core.database.get_session')
    def test_get_patterns_by_type(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule1 = MagicMock()
        rule1.pattern = "damaged"
        rule2 = MagicMock()
        rule2.pattern = "broken"

        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            rule1, rule2
        ]

        patterns = get_patterns_by_type(KnowledgeBaseRuleType.EXCLUSION, session=session)
        assert patterns == ["damaged", "broken"]

    @patch('sigmaprice.core.database.get_session')
    def test_is_excluded_by_kb_match(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule = MagicMock()
        rule.pattern = "damaged packaging"
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [rule]

        assert is_excluded_by_kb("Item with damaged packaging box", session) is True

    @patch('sigmaprice.core.database.get_session')
    def test_is_excluded_by_kb_no_match(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule = MagicMock()
        rule.pattern = "damaged packaging"
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [rule]

        assert is_excluded_by_kb("Brand new item in perfect condition", session) is False

    @patch('sigmaprice.core.database.get_session')
    def test_is_excluded_by_kb_empty_rules(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        assert is_excluded_by_kb("Any item", session) is False

    @patch('sigmaprice.core.database.get_session')
    def test_get_suffixes(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule1 = MagicMock()
        rule1.pattern = "SHADOW 3X"
        rule1.resolution = "SHADOW 3X OC"
        rule2 = MagicMock()
        rule2.pattern = "VENTUS 2X"
        rule2.resolution = "VENTUS 2X OC"

        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            rule1, rule2
        ]

        suffixes = get_suffixes(session=session)
        assert suffixes["SHADOW 3X"] == "SHADOW 3X OC"
        assert suffixes["VENTUS 2X"] == "VENTUS 2X OC"

    @patch('sigmaprice.core.database.get_session')
    def test_get_synonyms(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule1 = MagicMock()
        rule1.pattern = "BOX"
        rule1.resolution = "Retail"
        rule2 = MagicMock()
        rule2.pattern = "TRAY"
        rule2.resolution = "OEM"

        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            rule1, rule2
        ]

        synonyms = get_synonyms(session=session)
        assert synonyms["BOX"] == "Retail"
        assert synonyms["TRAY"] == "OEM"

    @patch('sigmaprice.core.database.get_session')
    def test_seed_default_rules_first_time(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        session.query.return_value.count.return_value = 0

        with patch('sigmaprice.knowledge.manager.KnowledgeBase') as mock_kb:
            rule = MagicMock()
            mock_kb.return_value = rule

            count = seed_default_rules(session=session)

            assert count > 0

    @patch('sigmaprice.core.database.get_session')
    def test_seed_default_rules_already_seeded(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.count.return_value = 25

        count = seed_default_rules(session=session)
        assert count == 0

    @patch('sigmaprice.core.database.get_session')
    def test_delete_rule_not_found(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None

        result = delete_rule(999, session=session)
        assert result is False

    @patch('sigmaprice.core.database.get_session')
    def test_delete_rule_success(self, mock_get_session):
        session = MagicMock()
        mock_get_session.return_value = session

        rule = MagicMock()
        rule.id = 1
        rule.rule_type = KnowledgeBaseRuleType.EXCLUSION
        rule.pattern = "test"
        session.query.return_value.filter.return_value.first.return_value = rule

        result = delete_rule(1, session=session)
        assert result is True
        assert session.delete.called
