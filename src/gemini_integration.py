"""
Google Gemini API와 MCP 서버 통합
자연언어로 NAS 파일 검색 및 조회
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from .ai_client import AIClient
from .mcp_server import NASSearchMCPServer
from .config import Config


logger = logging.getLogger(__name__)


class GeminiNASSearchClient(AIClient):
    """
    Google Gemini API를 이용한 NAS 검색 클라이언트
    
    자연언어 쿼리를 통해 MCP 도구를 호출하고
    결과를 Gemini와 협력하여 사용자에게 제공
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        클라이언트 초기화

        Args:
            api_key: Google API Key (환경변수 사용 권장)
        """
        # API Key 설정
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY를 설정하세요.\n"
                "방법 1: 환경변수 설정\n"
                "방법 2: .env 파일에 GOOGLE_API_KEY=... 추가"
            )

        # Gemini 클라이언트 초기화
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

        # MCP 서버 초기화
        Config.validate()
        self.mcp_server = NASSearchMCPServer()

        # 대화 히스토리
        self.conversation_history: List[Dict[str, Any]] = []

        # 시스템 프롬프트
        self.system_prompt = """당신은 사내 NAS 파일 검색 어시스턴트입니다.

사용자의 질문에 답하기 위해 다음 도구들을 사용할 수 있습니다:
- search_files: 파일명, 내용, 필터로 파일 검색
- list_directory: 디렉토리 탐색 및 파일 목록 조회
- get_file_info: 특정 파일의 상세 정보 조회
- preview_file: 텍스트 파일 미리보기

사용자의 요청을 분석하고 적절한 도구를 호출하여 답변을 제공하세요.
결과는 자연스럽고 유용한 한국어로 설명해주세요.

중요: 도구를 호출할 때는 다음 JSON 형식을 사용하세요:
{"tool_name": "...", "parameters": {...}}

예:
{"tool_name": "search_files", "parameters": {"query": "zip"}}
{"tool_name": "get_file_info", "parameters": {"file_path": "flutter.zip"}}"""

        logger.info("Gemini NAS Search Client initialized")

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        MCP 도구 정의 (Google Tool 형식)

        Returns:
            List[Dict]: Gemini API의 tools 파라미터에 전달할 스키마
        """
        return [
            {
                "name": "search_files",
                "description": (
                    "NAS에서 파일을 검색합니다. "
                    "파일명, 내용, 타입, 크기 등으로 필터링할 수 있습니다."
                ),
                "parameters": {
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
                "parameters": {
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
                            "description": "재귀 탐색 여부"
                        },
                        "page": {
                            "type": "integer",
                            "description": "페이지 번호"
                        },
                        "page_size": {
                            "type": "integer",
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
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "파일 경로"
                        },
                        "nas_name": {
                            "type": "string",
                            "description": "NAS 이름"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "preview_file",
                "description": (
                    "텍스트 파일의 내용을 미리봅니다. "
                    "인코딩을 자동으로 감지하고, 큰 파일은 자동으로 잘립니다."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "파일 경로"
                        },
                        "nas_name": {
                            "type": "string",
                            "description": "NAS 이름"
                        },
                        "max_bytes": {
                            "type": "integer",
                            "description": "최대 읽기 바이트"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]

    def chat(self, user_message: str) -> str:
        """
        사용자와 대화

        Args:
            user_message: 사용자의 메시지

        Returns:
            str: Gemini의 응답
        """
        logger.info(f"[User] {user_message}")

        # 대화 히스토리에 사용자 메시지 추가
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # 프롬프트 구성
        messages_text = self.system_prompt + "\n\n"
        for msg in self.conversation_history:
            role = "사용자" if msg["role"] == "user" else "어시스턴트"
            messages_text += f"{role}: {msg['content']}\n\n"

        # Gemini API 호출
        try:
            response = self.model.generate_content(
                messages_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )

            # 응답 처리
            return self._handle_response(response)

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)
            return f"오류: {str(e)}"

    def _handle_response(self, response) -> str:
        """
        Gemini 응답 처리

        도구 호출이 없으면 최종 응답 반환
        도구 호출이 있으면 실행 후 다시 Gemini에 전달

        Args:
            response: Gemini API 응답

        Returns:
            str: 최종 응답 텍스트
        """
        try:
            response_text = response.text if response else ""

            # 도구 호출 감지
            tool_calls = self._extract_tool_calls(response_text)

            if tool_calls:
                logger.info(f"[Tools] Gemini requested {len(tool_calls)} tool call(s)")

                # 도구 실행 결과 수집
                tool_results = []
                for tool_call in tool_calls:
                    logger.info(f"  - Calling {tool_call['tool_name']} with {tool_call['parameters']}")

                    # 도구 실행
                    result = self._execute_tool(tool_call["tool_name"], tool_call["parameters"])
                    tool_results.append(result)

                # 대화 히스토리에 응답 추가
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_text
                })

                # 도구 결과를 사용자 메시지로 추가
                tool_results_text = "도구 실행 결과:\n"
                for i, result in enumerate(tool_results, 1):
                    tool_results_text += f"{i}. {json.dumps(result, ensure_ascii=False)}\n"

                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results_text
                })

                # 다시 Gemini 호출 (최종 답변 받기)
                messages_text = self.system_prompt + "\n\n"
                for msg in self.conversation_history:
                    role = "사용자" if msg["role"] == "user" else "어시스턴트"
                    messages_text += f"{role}: {msg['content']}\n\n"

                final_response = self.model.generate_content(
                    messages_text,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=2048,
                    )
                )

                return self._handle_response(final_response)

            else:
                # 도구 호출 없음 - 최종 응답 반환
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_text
                })

                logger.info(f"[Gemini] {response_text[:100]}...")
                return response_text

        except Exception as e:
            logger.error(f"Response handling error: {str(e)}", exc_info=True)
            return f"응답 처리 중 오류: {str(e)}"

    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        응답 텍스트에서 도구 호출 추출

        Args:
            text: Gemini 응답 텍스트

        Returns:
            List[Dict]: 추출된 도구 호출 리스트
        """
        tool_calls = []

        # JSON 형식의 도구 호출 찾기
        import re
        json_pattern = r'\{"tool_name":\s*"([^"]+)",\s*"parameters":\s*({[^}]+})\}'

        matches = re.findall(json_pattern, text)
        for tool_name, params_str in matches:
            try:
                params = json.loads(params_str)
                tool_calls.append({
                    "tool_name": tool_name,
                    "parameters": params
                })
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool parameters: {params_str}")

        return tool_calls

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
        print("NAS 검색 MCP - Gemini AI 대화형 인터페이스")
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

                # Gemini와 대화
                response = self.chat(user_input)
                print(f"\nGemini: {response}\n")

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
        client = GeminiNASSearchClient()

        # 대화형 모드 시작
        client.interactive_chat()

    except ValueError as e:
        print(f"❌ 설정 오류: {str(e)}")
    except Exception as e:
        print(f"❌ 오류: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
