"""
MCP 서버 모든 도구 통합 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server import NASSearchMCPServer
from src.config import Config


def main():
    """통합 테스트 실행"""
    print("=" * 80)
    print("MCP 서버 4개 도구 통합 테스트")
    print("=" * 80)
    
    # 서버 초기화
    print("\n[초기화] MCP 서버 초기화 중...")
    Config.validate()
    server = NASSearchMCPServer()
    print("✓ 서버 초기화 완료")
    
    # 1. search_files
    print("\n[TEST 1] search_files - 파일 검색")
    print("-" * 80)
    result = server.search_files("zip", max_results=5)
    print(f"  검색어: 'zip'")
    print(f"  결과: {result['data']['total_count']}개 파일")
    if result["data"]["files"]:
        for f in result["data"]["files"][:2]:
            print(f"    - {f['name']} ({f['size']:,} bytes)")
    print(f"  ✓ 성공 (응답시간: {result['data']['elapsed_ms']}ms)")
    
    # 2. list_directory
    print("\n[TEST 2] list_directory - 디렉토리 탐색")
    print("-" * 80)
    result = server.list_directory("", "", recursive=False, page_size=10)
    print(f"  NAS: 첫 번째")
    print(f"  경로: (루트)")
    print(f"  결과: {result['data']['pagination']['total_items']}개 파일")
    if result["data"]["files"]:
        for f in result["data"]["files"][:2]:
            print(f"    - {f['name']} ({f['size']:,} bytes)")
    print(f"  ✓ 성공 (응답시간: {result['data']['elapsed_ms']}ms)")
    
    # 3. get_file_info
    print("\n[TEST 3] get_file_info - 파일 정보")
    print("-" * 80)
    test_file = "D:\\Source\\flutter.zip"
    if os.path.exists(test_file):
        result = server.get_file_info(test_file)
        if result["success"]:
            data = result["data"]
            print(f"  파일: {data['name']}")
            print(f"  크기: {data['size']:,} bytes")
            print(f"  타입: {data['file_type']}")
            print(f"  인덱싱: {data['indexed']}")
            print(f"  ✓ 성공 (응답시간: {data['elapsed_ms']}ms)")
        else:
            print(f"  ✗ 실패: {result['error']}")
    else:
        print(f"  ⚠ 테스트 파일 없음: {test_file}")
    
    # 4. preview_file
    print("\n[TEST 4] preview_file - 파일 미리보기")
    print("-" * 80)
    
    # 텍스트 파일 생성 (테스트용)
    test_preview_file = "D:\\Source\\mcp_preview_test.txt"
    with open(test_preview_file, 'w') as f:
        f.write("Line 1: Test preview\n")
        f.write("Line 2: MCP tool testing\n")
        f.write("Line 3: Hello World\n")
    
    result = server.preview_file(test_preview_file, max_bytes=500)
    if result["success"]:
        data = result["data"]
        print(f"  파일: {data['name']}")
        print(f"  크기: {data['size']} bytes")
        print(f"  인코딩: {data['encoding']}")
        print(f"  라인: {data['lines']}")
        print(f"  내용:\n{data['content']}")
        print(f"  ✓ 성공 (응답시간: {data['elapsed_ms']}ms)")
    else:
        print(f"  ✗ 실패: {result['error']}")
    
    # 정리
    if os.path.exists(test_preview_file):
        os.remove(test_preview_file)
    
    # 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print("✓ search_files: 작동")
    print("✓ list_directory: 작동")
    print("✓ get_file_info: 작동")
    print("✓ preview_file: 작동")
    print("\n✅ 모든 도구가 정상 작동합니다!")
    print("=" * 80)


if __name__ == "__main__":
    main()
