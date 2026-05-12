"""Абстрактные классы провайдеров для Matcher"""
from abc import ABC, abstractmethod
from typing import Any


class EmbeddingProvider(ABC):
    """Абстрактный провайдер для генерации эмбеддингов."""

    @abstractmethod
    def generate(self, text: str) -> list[float]:
        """Генерирует эмбеддинг для текста."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Возвращает размерность вектора."""
        pass


class WebResearchProvider(ABC):
    """Абстрактный провайдер для веб-поиска."""

    @abstractmethod
    def research(self, item: Any, query: str) -> dict:
        """
        Выполняет исследование товара в интернете.

        Returns:
            dict с ключами: 'found' (bool), 'info' (str), 'confidence' (float)
        """
        pass