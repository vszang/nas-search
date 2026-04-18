"""
Claude API와 MCP 서버 통합
자연언어로 NAS 파일 검색 및 조회
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from anthropic import Anthropic

from .ai_client import AIClient, AIClientFactory
from .mcp_server import NASSearchMCPServer
from .config import Config


logger = logging.getLogger(__name__)


class ClaudeNASSearchClient(AIClient):
    """
    Claude API를 이용한 NAS 검색 클라이언트
    
    자연언어 쿼리를 통해 MCP 도구를 호출하고
    결과를 Claude와 협력하여 사용자에게 제공
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        클라이언트 초기화
        
        Args:
            api_key: Anthropic API Key (환경변수 사용 권장)
        """
        # API Key 설정
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY를 설정하세요.\n"
                "방법 1: 환경변수 설정\n"
                "방법 2: .env 파일에 ANTHROPIC_API_KEY=sk-... 추가"
            )
        
        # Claude 클라이언트 초기화
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-haiku-4-5-20251001"  # 기본 모델
        
        # MCP 서버 초기화
        Config.validate()
        self.mcp_server = NASSearchMCPServer()
        
        # 대화 히스토리
        self.conversation_history: List[Dict[str, Any]] = []
        
        # 시스템 프롬프트
        self.system_prompt = """당신은 사내 NAS 파일 검색 어시스턴트입니다.

사용자의 질문에 답하기 위해 다음 도구들을 사용할 수 있습니다:
- search_files: 파일명 또는 파일 내용으로 검색
- list_directory: 디렉토리 탐색 및 파일 목록 조회
- get_file_info: 특정 파일의 상세 정보 조회
- preview_file: 파일 내용 미리보기 (PDF, DOCX, XLSX, PPTX, HWP, TXT, CSV, JSON, 코드 등 지원)

중요 규칙:
- 파일 내용에 대해 질문받으면 반드시 preview_file 도구를 호출하세요. 스스로 "지원 안 된다"고 판단하지 마세요.
- PDF, 엑셀, 워드, 파워포인트, HWP 파일도 preview_file로 내용 추출이 가능합니다.
- 파일을 찾은 후 내용 요약이나 확인이 필요하면 preview_file을 추가로 호출하세요.

사용자의 요청을 분석하고 적절한 도구를 호출하여 답변을 제공하세요.
결과는 자연스럽고 유용한 한국어로 설명해주세요."""
        
        logger.info("Claude NAS Search Client initialized")
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        MCP 도구 정의 (JSON Schema)
        
        Returns:
            List[Dict]: Claude API의 tools 파라미터에 전달할 스키마
        """
        return [
            {
                "name": "search_files",
                "description": (
                    "NAS에서 파일을 검색합니다. "
                    "파일명, 내용, 타입, 크기 등으로 필터링할 수 있습니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색 키워드 (파일명 또는 내용)"
                        },
                        "file_type": {
                            "type": "string",
                            "enum": ["document", "text", "image", "video", "audio", "archive", "code"],
                            "description": "파일 타입 필터 (선택사항)"
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 50,
                            "description": "최대 결과 수"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_directory",
                "description": (
                    "NAS 디렉토리를 탐색하여 파일 목록을 조회합니다. "
                    "페이지네이션을 지원합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "nas_name": {
                            "type": "string",
                            "description": "NAS 이름 (생략하면 첫 번째 NAS)"
                        },
                        "path": {
                            "type": "string",
                            "description": "디렉토리 경로 (기본값: 루트)"
                        },
                        "recursive": {
                            "type": "boolean",
                            "default": False,
                            "description": "재귀 탐색 여부"
                        },
                        "page": {
                            "type": "integer",
                            "default": 1,
                            "description": "페이지 번호"
                        },
                        "page_size": {
                            "type": "integer",
                            "default": 100,
                            "description": "페이지당 항목 수"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_file_info",
                "description": (
                    "특정 파일의 상세 정보를 조회합니다. "
                    "파일 크기, 타입, 수정일, 인덱싱 상태 등을 반환합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "파일 경로"
                        },
                        "nas_name": {
                            "type": "string",
                            "default": "LOCAL",
                            "description": "NAS 이름"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "preview_file",
                "description": (
                    "파일 내용을 미리봅니다. "
                    "PDF, DOCX, XLSX, PPTX, HWP, TXT, CSV, JSON, 코드 파일 등 다양한 형식을 지원합니다. "
                    "PDF와 오피스 문서는 텍스트를 자동 추출합니다. "
                    "파일 내용 확인이나 요약이 필요할 때 반드시 이 도구를 호출하세요."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "파일 경로"
                        },
                        "nas_name": {
                            "type": "string",
                            "default": "LOCAL",
                            "description": "NAS 이름"
                        },
                        "max_bytes": {
                            "type": "integer",
                            "default": 1024,
                            "description": "최대 읽기 바이트"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]
    
    def chat(self, user_message: str, model: str = None) -> str:
        """
        사용자와 대화

        Args:
            user_message: 사용자의 메시지
            model: 사용할 모델 (None이면 기본 모델 사용)

        Returns:
            str: Claude의 응답
        """
        if model:
            self.model = model
        logger.info(f"[User] {user_message} | model={self.model}")

        # 대화 히스토리에 사용자 메시지 추가
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Claude API 호출
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            tools=self.get_tools_schema(),
            messages=self.conversation_history
        )
        
        # 응답 처리
        return self._handle_response(response)
    
    def _handle_response(self, response) -> str:
        """
        Claude 응답 처리
        
        도구 호출이 없으면 최종 응답 반환
        도구 호출이 있으면 실행 후 다시 Claude에 전달
        
        Args:
            response: Claude API 응답
        
        Returns:
            str: 최종 응답 텍스트
        """
        # 응답 종료 케이스
        if response.stop_reason == "end_turn":
            # 텍스트 응답만 추출
            text_response = ""
            for content in response.content:
                if hasattr(content, "text"):
                    text_response = content.text
                    break
            
            # 대화 히스토리에 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": text_response
            })
            
            logger.info(f"[Claude] {text_response[:100]}...")
            return text_response
        
        # 도구 호출 케이스
        if response.stop_reason == "tool_use":
            logger.info(f"[Tools] Claude requested tool calls")
            
            # 도구 호출 결과 수집
            tool_results = []
            for content in response.content:
                if content.type == "tool_use":
                    logger.info(f"  - Calling {content.name} with {content.input}")
                    print(f"[TOOL CALL] {content.name} | input: {content.input}", flush=True)

                    # 도구 실행
                    result = self._execute_tool(content.name, content.input)

                    result_preview = json.dumps(result, ensure_ascii=False)[:300]
                    print(f"[TOOL RESULT] {content.name} | result: {result_preview}", flush=True)
                    logger.info(f"  - Result: {result_preview}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": json.dumps(result, ensure_ascii=False, indent=2)
                    })
            
            # 대화 히스토리에 assistant 응답 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            
            # 도구 결과를 사용자 메시지로 추가
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })
            
            # 다시 Claude 호출 (최종 답변 받기)
            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.get_tools_schema(),
                messages=self.conversation_history
            )
            
            return self._handle_response(final_response)
        
        # 예외 케이스
        logger.warning(f"Unexpected stop reason: {response.stop_reason}")
        return "응답 처리 중 오류가 발생했습니다."
    
    def _execute_tool(self, tool_name: str, tool_input: dict) -> Dict[str, Any]:
        """
        MCP 도구 실행
        
        Args:
            tool_name: 도구 이름
            tool_input: 도구 입력 파라미터
        
        Returns:
            Dict: 도구 실행 결과
        """
        try:
            # MCP 서버의 도구 호출
            tool_method = getattr(self.mcp_server, tool_name)
            result = tool_method(**tool_input)
            
            logger.info(f"[Tool Result] {tool_name}: success={result.get('success', 'N/A')}")
            
            return result
        
        except Exception as e:
            logger.error(f"[Tool Error] {tool_name}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "TOOL_EXECUTION_ERROR"
            }
    
    def interactive_chat(self):
        """
        대화형 모드 (REPL)
        """
        print("\n" + "=" * 80)
        print("NAS 검색 MCP - Claude AI 대화형 인터페이스")
        print("=" * 80)
        print("\n💡 팁:")
        print("  - '종료', 'exit', 'quit'를 입력하면 종료합니다.")
        print("  - 자연스러운 질문 예:")
        print("    * ZIP 파일을 찾아줄 수 있을까?")
        print("    * 100MB 이상의 파일이 있나요?")
        print("    * flutter.zip 파일의 크기는?")
        print("    * test.txt 파일 내용 보여줄 수 있어?")
        print("\n" + "-" * 80 + "\n")
        
        while True:
            try:
                user_input = input("당신: ").strip()
                
                # 종료 조건
                if user_input.lower() in ['exit', 'quit', '종료', 'esc']:
                    print("\n대화를 종료합니다. 감사합니다! 👋")
                    break
                
                # 빈 입력 무시
                if not user_input:
                    continue
                
                # Claude와 대화
                response = self.chat(user_input)
                print(f"\nClaude: {response}\n")
            
            except KeyboardInterrupt:
                print("\n\n대화를 중단합니다. 👋")
                break
            except Exception as e:
                logger.error(f"Chat error: {str(e)}", exc_info=True)
                print(f"\n❌ 오류: {str(e)}\n")
    
    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """대화 히스토리 조회"""
        return self.conversation_history.copy()


def main():
    """테스트 메인 함수"""
    try:
        # 클라이언트 초기화
        client = ClaudeNASSearchClient()
        
        # 대화형 모드 시작
        client.interactive_chat()
    
    except ValueError as e:
        print(f"❌ 설정 오류: {str(e)}")
    except Exception as e:
        print(f"❌ 오류: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
