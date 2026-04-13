"""
MCP 서버의 list_directory 도구 테스트
"""

import sys
import os
import pytest
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server import NASSearchMCPServer
from src.config import Config


class TestListDirectory:
    """list_directory 도구 테스트"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        Config.validate()
        cls.server = NASSearchMCPServer()
    
    def test_list_root_directory(self):
        """루트 디렉토리 나열"""
        print("\n[TEST 1] 루트 디렉토리 나열")
        
        result = self.server.list_directory("LOCAL", "", recursive=False)
        
        assert result["success"] == True, f"조회 실패: {result}"
        
        data = result["data"]
        assert "files" in data, "files 필드 없음"
        assert "directories" in data, "directories 필드 없음"
        assert "pagination" in data, "pagination 필드 없음"
        
        files = data["files"]
        dirs = data["directories"]
        pagination = data["pagination"]
        
        print(f"  ✓ 파일: {pagination['total_items']}개")
        print(f"  ✓ 디렉토리: {len(dirs)}개")
        print(f"  ✓ 응답시간: {data.get('elapsed_ms', 'N/A')}ms")
        
        assert pagination["total_items"] > 0, "파일이 0개?"
        assert pagination["page"] > 0, "페이지는 1 이상이어야 함"
    
    def test_list_with_pagination(self):
        """페이지네이션 테스트"""
        print("\n[TEST 2] 페이지네이션 테스트")
        
        # 첫 번째 페이지
        result1 = self.server.list_directory("LOCAL", "", page=1, page_size=5)
        assert result1["success"] == True
        
        # 두 번째 페이지
        result2 = self.server.list_directory("LOCAL", "", page=2, page_size=5)
        assert result2["success"] == True
        
        data1 = result1["data"]
        data2 = result2["data"]
        
        print(f"  ✓ Page 1: {len(data1['files'])} 파일")
        print(f"  ✓ Page 2: {len(data2['files'])} 파일")
        print(f"  ✓ Total: {data1['pagination']['total_items']} 파일")
        
        # 페이지 정보 검증
        assert data1["pagination"]["page"] == 1
        assert data2["pagination"]["page"] == 2
        assert len(data1["files"]) <= 5
        assert len(data2["files"]) <= 5
    
    def test_list_recursive_vs_non_recursive(self):
        """재귀 vs 비재귀 탐색"""
        print("\n[TEST 3] 재귀 탐색 테스트")
        
        # 비재귀
        result_non_rec = self.server.list_directory("LOCAL", "", recursive=False)
        assert result_non_rec["success"] == True
        
        # 재귀 (같은 경로지만 recursive=True)
        result_rec = self.server.list_directory("LOCAL", "", recursive=True)
        assert result_rec["success"] == True
        
        count_non_rec = result_non_rec["data"]["pagination"]["total_items"]
        count_rec = result_rec["data"]["pagination"]["total_items"]
        
        print(f"  ✓ 비재귀: {count_non_rec} 파일")
        print(f"  ✓ 재귀: {count_rec} 파일")
    
    def test_list_response_format(self):
        """응답 포맷 검증"""
        print("\n[TEST 4] 응답 포맷 검증")
        
        result = self.server.list_directory("LOCAL", "")
        
        # 최상위 레벨
        assert "success" in result
        assert "data" in result
        assert isinstance(result["success"], bool)
        
        # data 필드
        data = result["data"]
        assert "files" in data
        assert "directories" in data
        assert "pagination" in data
        assert "elapsed_ms" in data
        
        # 파일 포맷
        for file_obj in data["files"]:
            assert "name" in file_obj
            assert "path" in file_obj
            assert "size" in file_obj
            assert "modified" in file_obj
            assert "file_type" in file_obj
        
        # pagination 포맷
        pagination = data["pagination"]
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total_items" in pagination
        assert "total_pages" in pagination
        
        print(f"  ✓ 응답 포맷 유효")
    
    def test_list_nas_not_found(self):
        """존재하지 않는 NAS 처리"""
        print("\n[TEST 5] 존재하지 않는 NAS 처리")
        
        result = self.server.list_directory("NONEXISTENT_NAS", "")
        
        assert result["success"] == False, "에러 응답이어야 함"
        assert result["error_code"] == "NAS_NOT_FOUND"
        
        print(f"  ✓ 에러 코드: {result['error_code']}")
        print(f"  ✓ 에러 메시지: {result['error']}")
    
    def test_list_path_traversal_protection(self):
        """경로 포함 공격 방어"""
        print("\n[TEST 6] 경로 포함 공격 방어")
        
        result = self.server.list_directory("LOCAL", "../etc/passwd")
        
        assert result["success"] == False, "에러 응답이어야 함"
        assert result["error_code"] == "INVALID_PATH"
        
        print(f"  ✓ 경로 공격 차단: {result['error']}")
    
    def test_list_empty_path(self):
        """빈 경로 처리 (루트)"""
        print("\n[TEST 7] 빈 경로 처리")
        
        result = self.server.list_directory("LOCAL", "")
        
        assert result["success"] == True
        assert result["data"]["pagination"]["total_items"] > 0
        
        print(f"  ✓ 루트 디렉토리: {result['data']['pagination']['total_items']} 파일")
    
    def test_list_performance(self):
        """성능 테스트"""
        print("\n[TEST 8] 성능 검증 (<500ms)")
        
        result = self.server.list_directory("LOCAL", "")
        
        assert result["success"] == True
        
        elapsed_ms = result["data"].get("elapsed_ms", 0)
        print(f"  ✓ 응답시간: {elapsed_ms}ms")
        
        # 목표: 500ms 이내 (더 큰 디렉토리이므로 search_files보다 느림)
        assert elapsed_ms < 500, f"성능 목표 초과: {elapsed_ms}ms"


def main():
    """테스트 실행"""
    print("=" * 70)
    print("MCP list_directory 도구 테스트")
    print("=" * 70)
    
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    main()
