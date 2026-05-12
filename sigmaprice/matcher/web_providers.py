"""Провайдеры веб-исследований"""
from sigmaprice.matcher.providers import WebResearchProvider
from sigmaprice.core.logger import get_logger
from sigmaprice.core.types import RawItem

logger = get_logger(__name__)


class ClaudeResearchProvider(WebResearchProvider):
    """Веб-поиск через Claude API."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Claude API key is required")
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

    def research(self, item: RawItem, query: str) -> dict:
        """Выполняет поиск через Claude API."""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"Искать информацию о товаре: {query}"
                    }
                ]
            )
            return {
                "found": True,
                "info": response.content[0].text,
                "confidence": 0.9
            }
        except Exception as e:
            logger.error(f"Claude research error: {e}")
            return {"found": False, "info": str(e), "confidence": 0.0}


class OpenAIResearchProvider(WebResearchProvider):
    """Веб-поиск через OpenAI API."""

    def __init__(self, api_key: str | None):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        try:
            import openai
            openai.api_key = api_key
            self.client = openai
        except ImportError:
            raise ImportError("openai package required: pip install openai")

    def research(self, item: RawItem, query: str) -> dict:
        """Выполняет поиск через OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": f"Искать информацию о товаре: {query}"}
                ],
                max_tokens=500
            )
            return {
                "found": True,
                "info": response.choices[0].message.content,
                "confidence": 0.9
            }
        except Exception as e:
            logger.error(f"OpenAI research error: {e}")
            return {"found": False, "info": str(e), "confidence": 0.0}


class OllamaResearchProvider(WebResearchProvider):
    """Локальный веб-поиск через Ollama."""

    def __init__(self, url: str = "http://localhost:11434", model: str = "llama3"):
        self.url = url
        self.model = model

    def research(self, item: RawItem, query: str) -> dict:
        """Выполняет поиск через локальный Ollama."""
        try:
            import requests
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"Искать информацию о товаре: {query}",
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                return {
                    "found": True,
                    "info": result.get("response", ""),
                    "confidence": 0.8
                }
            return {"found": False, "info": f"HTTP {response.status_code}", "confidence": 0.0}
        except Exception as e:
            logger.error(f"Ollama research error: {e}")
            return {"found": False, "info": str(e), "confidence": 0.0}