"""
AI 클라이언트 팩토리 및 등록
"""

from .ai_client import AIClient, AIClientFactory
from .claude_integration import ClaudeNASSearchClient
from .gemini_integration import GeminiNASSearchClient


# 클라이언트 등록
AIClientFactory.register("claude", ClaudeNASSearchClient)
AIClientFactory.register("gemini", GeminiNASSearchClient)


__all__ = [
    "AIClient",
    "AIClientFactory",
    "ClaudeNASSearchClient",
    "GeminiNASSearchClient",
]
