"""
AI 클라이언트 추상 인터페이스
Claude, Gemini 등 여러 LLM API를 통일된 인터페이스로 제공
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AIClient(ABC):
    """모든 AI 클라이언트가 상속해야 하는 추상 클래스"""

    @abstractmethod
    def __init__(self):
        """클라이언트 초기화"""
        pass

    @abstractmethod
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        MCP 도구들을 AI API 형식으로 변환하여 반환
        
        Returns:
            도구 정의 리스트
        """
        pass

    @abstractmethod
    def chat(self, message: str) -> str:
        """
        사용자 메시지를 처리하고 AI 응답 반환
        필요에 따라 MCP 도구를 자동으로 호출
        
        Args:
            message: 사용자 메시지
            
        Returns:
            AI 응답
        """
        pass

    @abstractmethod
    def interactive_chat(self) -> None:
        """대화형 REPL 루프 시작"""
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """대화 히스토리 초기화"""
        pass

    @abstractmethod
    def get_history(self) -> List[Dict[str, str]]:
        """
        현재 대화 히스토리 반환
        
        Returns:
            대화 히스토리 (role/content 형식)
        """
        pass


class AIClientFactory:
    """AI 클라이언트 팩토리 - 원하는 AI API 클라이언트를 선택"""

    _CLIENTS = {}

    @classmethod
    def register(cls, name: str, client_class: type):
        """새로운 클라이언트 등록"""
        cls._CLIENTS[name] = client_class

    @classmethod
    def create(cls, provider: str = "claude", **kwargs) -> AIClient:
        """
        AI 클라이언트 생성
        
        Args:
            provider: AI 제공사 ("claude", "gemini")
            **kwargs: 추가 설정
            
        Returns:
            AIClient 인스턴스
            
        Raises:
            ValueError: 지원하지 않는 provider인 경우
        """
        provider = provider.lower()

        if provider not in cls._CLIENTS:
            supported = ", ".join(cls._CLIENTS.keys())
            raise ValueError(
                f"지원하지 않는 AI 제공사: {provider}\n"
                f"지원 목록: {supported}"
            )

        client_class = cls._CLIENTS[provider]
        return client_class(**kwargs)

    @classmethod
    def list_providers(cls) -> List[str]:
        """지원하는 AI 제공사 목록"""
        return list(cls._CLIENTS.keys())
