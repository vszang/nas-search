"""
Claude API 통합 테스트
자연언어 쿼리를 통한 MCP 도구 호출 검증
"""

import sys
import os
import time
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.claude_integration import ClaudeNASSearchClient
from src.config import Config


def test_client_initialization():
    """클라이언트 초기화 테스트"""
    print("\n[TEST 1] Claude 클라이언트 초기화")
    print("-" * 80)
    
    try:
        client = ClaudeNASSearchClient()
        print("✓ 클라이언트 초기화 성공")
        print(f"  - 모델: {client.model}")
        print(f"  - 도구 개수: {len(client.get_tools_schema())}")
        return client
    except ValueError as e:
        print(f"✗ 초기화 실패: {e}")
        print("\n💡 API Key 설정 방법:")
        print("  1. 환경변수 설정: export ANTHROPIC_API_KEY=sk-...")
        print("  2. .env 파일: ANTHROPIC_API_KEY=sk-... 추가")
        sys.exit(1)


def test_tools_schema():
    """도구 정의 스키마 테스트"""
    print("\n[TEST 2] 도구 정의 스키마 검증")
    print("-" * 80)
    
    client = ClaudeNASSearchClient()
    tools = client.get_tools_schema()
    
    print(f"✓ 총 {len(tools)}개 도구 정의")
    
    for tool in tools:
        print(f"\n  도구: {tool['name']}")
        print(f"    설명: {tool['description'][:50]}...")
        
        required = tool['input_schema'].get('required', [])
        properties = tool['input_schema'].get('properties', {})
        
        print(f"    필수 파라미터: {required if required else '없음'}")
        print(f"    전체 파라미터: {list(properties.keys())}")


def test_simple_search():
    """간단한 검색 테스트"""
    print("\n[TEST 3] 간단한 파일 검색")
    print("-" * 80)
    
    client = ClaudeNASSearchClient()
    
    print("사용자: 'ZIP 파일 찾아줄 수 있을까?'")
    print("처리 중...")
    
    start_time = time.time()
    
    try:
        response = client.chat("ZIP 파일 찾아줄 수 있을까?")
        elapsed = time.time() - start_time
        
        print(f"\nClaude: {response}")
        print(f"\n✓ 성공 (소요시간: {elapsed:.2f}초)")
        
        return True
    except Exception as e:
        print(f"\n✗ 실패: {str(e)}")
        return False


def test_filter_search():
    """필터를 포함한 검색 테스트"""
    print("\n[TEST 4] 필터 포함 검색")
    print("-" * 80)
    
    client = ClaudeNASSearchClient()
    
    print("사용자: '텍스트 파일을 찾아줄 수 있나요?'")
    print("처리 중...")
    
    start_time = time.time()
    
    try:
        response = client.chat("텍스트 파일을 찾아줄 수 있나요?")
        elapsed = time.time() - start_time
        
        print(f"\nClaude: {response}")
        print(f"\n✓ 성공 (소요시간: {elapsed:.2f}초)")
        
        return True
    except Exception as e:
        print(f"\n✗ 실패: {str(e)}")
        return False


def test_file_info():
    """파일 정보 조회 테스트"""
    print("\n[TEST 5] 파일 정보 조회")
    print("-" * 80)
    
    client = ClaudeNASSearchClient()
    
    print("사용자: 'flutter.zip 파일의 크기는?'")
    print("처리 중...")
    
    start_time = time.time()
    
    try:
        response = client.chat("flutter.zip 파일의 크기는?")
        elapsed = time.time() - start_time
        
        print(f"\nClaude: {response}")
        print(f"\n✓ 성공 (소요시간: {elapsed:.2f}초)")
        
        return True
    except Exception as e:
        print(f"\n✗ 실패: {str(e)}")
        return False


def test_multi_turn_conversation():
    """다중 턴 대화 테스트"""
    print("\n[TEST 6] 다중 턴 대화")
    print("-" * 80)
    
    client = ClaudeNASSearchClient()
    
    queries = [
        "가장 큰 파일이 뭔가요?",
        "그 파일의 타입은?",
        "언제 수정되었나요?"
    ]
    
    try:
        for i, query in enumerate(queries, 1):
            print(f"\n턴 {i}:")
            print(f"사용자: '{query}'")
            
            start_time = time.time()
            response = client.chat(query)
            elapsed = time.time() - start_time
            
            print(f"Claude: {response}")
            print(f"(소요시간: {elapsed:.2f}초)")
        
        print(f"\n✓ 성공 (대화 히스토리 길이: {len(client.get_history())})")
        
        return True
    except Exception as e:
        print(f"\n✗ 실패: {str(e)}")
        return False


def test_conversation_history():
    """대화 히스토리 관리 테스트"""
    print("\n[TEST 7] 대화 히스토리 관리")
    print("-" * 80)
    
    client = ClaudeNASSearchClient()
    
    # 초기 상태
    print(f"초기 히스토리 길이: {len(client.get_history())}")
    
    # 첫 번째 쿼리
    try:
        client.chat("ZIP 파일 찾기")
        print(f"첫 번째 쿼리 후: {len(client.get_history())} 항목")
        
        # 두 번째 쿼리
        client.chat("텍스트 파일 찾기")
        print(f"두 번째 쿼리 후: {len(client.get_history())} 항목")
        
        # 히스토리 초기화
        client.clear_history()
        print(f"초기화 후: {len(client.get_history())} 항목")
        
        if len(client.get_history()) == 0:
            print("✓ 성공")
            return True
        else:
            print("✗ 실패: 초기화되지 않음")
            return False
    
    except Exception as e:
        print(f"✗ 실패: {str(e)}")
        return False


def test_error_handling():
    """에러 처리 테스트"""
    print("\n[TEST 8] 에러 처리")
    print("-" * 80)
    
    client = ClaudeNASSearchClient()
    
    try:
        # 잘못된 파일 경로
        response = client.chat("'존재하지않는파일.txt' 파일의 정보는?")
        print(f"Claude: {response}")
        print("✓ 에러 처리 성공")
        
        return True
    except Exception as e:
        print(f"✗ 실패: {str(e)}")
        return False


def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 80)
    print("Claude API 통합 테스트")
    print("=" * 80)
    
    Config.validate()
    
    # 테스트 실행
    tests = [
        ("클라이언트 초기화", test_client_initialization),
        ("도구 정의 스키마", test_tools_schema),
        ("간단한 검색", test_simple_search),
        ("필터 포함 검색", test_filter_search),
        ("파일 정보 조회", test_file_info),
        ("다중 턴 대화", test_multi_turn_conversation),
        ("대화 히스토리", test_conversation_history),
        ("에러 처리", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if test_name == "클라이언트 초기화":
                test_client_initialization()
            elif test_name == "도구 정의 스키마":
                test_tools_schema()
            elif test_name == "간단한 검색":
                success = test_simple_search()
                results.append((test_name, success))
            elif test_name == "필터 포함 검색":
                success = test_filter_search()
                results.append((test_name, success))
            elif test_name == "파일 정보 조회":
                success = test_file_info()
                results.append((test_name, success))
            elif test_name == "다중 턴 대화":
                success = test_multi_turn_conversation()
                results.append((test_name, success))
            elif test_name == "대화 히스토리":
                success = test_conversation_history()
                results.append((test_name, success))
            elif test_name == "에러 처리":
                success = test_error_handling()
                results.append((test_name, success))
        except Exception as e:
            print(f"✗ 테스트 실행 중 오류: {str(e)}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {test_name}")
    
    print(f"\n총 {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("\n✅ 모든 테스트 통과!")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")


if __name__ == "__main__":
    main()
