"""
AI API 선택형 대화형 채팅 예제
Claude, Gemini 등 다양한 AI API를 지원
"""

import sys
import os
import argparse
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.ai_factory import AIClientFactory
from src.config import Config


def print_header(ai_provider: str):
    """헤더 출력"""
    print("\n" + "=" * 80)
    print(f"🔍 NAS 파일 검색 - {ai_provider.upper()} AI 챗봇")
    print("=" * 80)
    print("\n💬 자연언어로 파일을 검색해보세요!")
    print("\n예시:")
    print("  - ZIP 파일을 찾아줄 수 있을까?")
    print("  - 100MB 이상 500MB 이하의 파일이 있나요?")
    print("  - 텍스트 파일의 내용을 보여줄 수 있어?")
    print("  - 가장 큰 파일이 뭔가요?")
    print("\n명령어:")
    print("  - exit, quit, 종료: 채팅 종료")
    print("  - history: 대화 기록 확인")
    print("  - clear: 대화 기록 초기화")
    print("  - help: 도움말")
    print("\n" + "-" * 80 + "\n")


def print_history(history):
    """대화 기록 출력"""
    if not history:
        print("대화 기록이 없습니다.\n")
        return

    print("\n📋 대화 기록:")
    print("-" * 80)

    for i, msg in enumerate(history, 1):
        role = msg.get('role', '?')
        content = msg.get('content', '?')

        if isinstance(content, str):
            display_content = content[:60] + "..." if len(content) > 60 else content
        else:
            display_content = f"[{type(content).__name__}]"

        print(f"{i}. [{role.upper()}] {display_content}")

    print("-" * 80 + "\n")


def handle_special_command(command, client):
    """특수 명령어 처리"""
    if command.lower() in ['exit', 'quit', '종료']:
        return 'exit'

    elif command.lower() == 'history':
        print_history(client.get_history())
        return None

    elif command.lower() == 'clear':
        client.clear_history()
        print("✓ 대화 기록이 초기화되었습니다.\n")
        return None

    elif command.lower() in ['help', 'h', '도움']:
        print("""
📚 사용 가능한 명령어:
  - exit, quit, 종료: 프로그램 종료
  - history: 이전 대화 기록 표시
  - clear: 대화 기록 초기화
  - help: 이 도움말 표시

🎯 질문 예시:
  1. 파일 검색
     - "ZIP 파일을 찾아줄 수 있을까?"
     - "텍스트 파일이 있어?"

  2. 필터 검색
     - "100MB 이상 500MB 이하의 파일을 찾아줄 수 있을까?"
     - "가장 최근에 수정된 파일이 뭔가요?"

  3. 파일 정보
     - "flutter.zip 파일의 크기는?"
     - "text.txt 파일이 어디에 있어?"

  4. 파일 미리보기
     - "README.md 파일 내용 보여줄 수 있어?"
        """)
        return None

    return None


def interactive_chat(ai_provider: str = "claude"):
    """대화형 채팅 모드"""

    try:
        # 클라이언트 초기화
        print(f"\n🚀 {ai_provider.upper()} AI 클라이언트 초기화 중...")
        client = AIClientFactory.create(ai_provider)
        print("✓ 클라이언트 초기화 완료")

        # 현재 사용 가능한 도구 표시
        tools = client.get_tools_schema()
        print(f"✓ {len(tools)}개의 도구 로드됨:", end=" ")
        print(", ".join([t['name'] for t in tools]))

    except ValueError as e:
        print(f"\n❌ 초기화 실패: {e}")
        print("\n💡 문제 해결:")
        print(f"  1. API Key 확인")
        print(f"     - 환경변수: export {get_api_key_env_name(ai_provider)}=...")
        print(f"     - 또는 .env 파일: {get_api_key_env_name(ai_provider)}=...")
        print(f"  2. .env 파일 위치: 프로젝트 루트에 생성하세요")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        sys.exit(1)

    # 헤더 출력
    print_header(ai_provider)

    # 대화 루프
    turn = 0

    while True:
        try:
            # 사용자 입력
            user_input = input("👤 당신: ").strip()

            if not user_input:
                print()
                continue

            # 특수 명령어 확인
            result = handle_special_command(user_input, client)
            if result == 'exit':
                break
            elif result is None and user_input.lower() in ['exit', 'quit', '종료', 'history', 'clear', 'help', 'h', '도움']:
                continue

            # AI와 대화
            turn += 1
            print(f"\n🤖 {ai_provider.upper()} (처리 중...)  ", end="", flush=True)

            try:
                response = client.chat(user_input)

                # 기존 프롬프트 지우고 응답 출력
                print("\r", end="")
                print(f"🤖 {ai_provider.upper()}: {response}\n")

            except Exception as e:
                print(f"\r❌ 오류 발생: {str(e)}\n")

                if "401" in str(e) or "authentication" in str(e).lower():
                    print("💡 API 인증 실패: API Key를 확인해주세요.\n")
                elif "rate" in str(e).lower():
                    print("💡 요청 제한: 잠시 후 다시 시도해주세요.\n")
                else:
                    print("💡 문제가 지속되면 API 설정을 다시 확인해주세요.\n")

        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다.")
            break

        except Exception as e:
            print(f"\n❌ 예상치 못한 오류: {e}")
            continue

    # 종료 메시지
    print("\n" + "=" * 80)
    print(f"✓ {turn}번의 대화 후 종료되었습니다.")
    print("감사합니다!")
    print("=" * 80 + "\n")


def demo_mode(ai_provider: str = "claude"):
    """데모 모드 (자동 실행)"""

    print(f"\n🚀 {ai_provider.upper()} 데모 모드 시작...")
    print("-" * 80)

    try:
        client = AIClientFactory.create(ai_provider)

        demo_queries = [
            ("ZIP 파일을 찾아줄 수 있을까?", "ZIP 파일 검색"),
            ("텍스트 파일이 있어?", "텍스트 파일 검색"),
            ("flutter.zip 파일의 크기는?", "파일 정보 조회"),
        ]

        for query, description in demo_queries:
            print(f"\n📝 {description}")
            print(f"질문: {query}")
            print("응답:", end=" ", flush=True)

            try:
                response = client.chat(query)
                print(response[:100] + "..." if len(response) > 100 else response)
            except Exception as e:
                print(f"[오류] {str(e)[:60]}...")

    except Exception as e:
        print(f"❌ 데모 실행 실패: {e}")


def get_api_key_env_name(ai_provider: str) -> str:
    """AI 제공사에 따른 API Key 환경변수 이름 반환"""
    if ai_provider.lower() == "claude":
        return "ANTHROPIC_API_KEY"
    elif ai_provider.lower() == "gemini":
        return "GOOGLE_API_KEY"
    else:
        return "API_KEY"


def main():
    """메인 함수"""

    # 설정 검증
    Config.validate()

    # 명령라인 인자 처리
    parser = argparse.ArgumentParser(
        description="NAS 파일 검색 - AI 챗봇",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  # Claude API로 대화형 모드 (기본값)
  python example_chat.py

  # Gemini API로 대화형 모드
  python example_chat.py --provider gemini

  # 데모 모드
  python example_chat.py --demo

  # Gemini 데모 모드
  python example_chat.py --provider gemini --demo

  # 지원되는 AI 제공사 목록
  python example_chat.py --list-providers
        """
    )

    parser.add_argument(
        "--provider",
        default="claude",
        choices=["claude", "gemini"],
        help="AI API 제공사 (기본값: claude)"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="데모 모드 실행 (자동)"
    )

    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="지원되는 AI 제공사 목록"
    )

    args = parser.parse_args()

    # 지원되는 제공사 목록
    if args.list_providers:
        providers = AIClientFactory.list_providers()
        print("\n지원되는 AI 제공사:")
        for provider in providers:
            print(f"  - {provider}")
        return

    # 데모 모드
    if args.demo:
        demo_mode(args.provider)
        return

    # 대화형 모드
    interactive_chat(args.provider)


if __name__ == "__main__":
    main()
