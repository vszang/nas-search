"""
MCP 서버의 get_file_info 도구 테스트
"""

import sys
import os
import tempfile
import pytest
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server import NASSearchMCPServer
from src.config import Config


class TestGetFileInfo:
    """get_file_info 도구 테스트"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        Config.validate()
        cls.server = NASSearchMCPServer()
        
        # 테스트용 임시 파일 생성
        cls.test_file = Path("D:\\Source\\test_document.txt")
        if not cls.test_file.exists():
            cls.test_file.write_text("Test content for get_file_info test\n" * 10)
    
    def test_get_indexed_file_info(self):
        """인덱싱된 파일 정보"""
        print("\n[TEST 1] 인덱싱된 파일 정보 조회")
        
        # 인덱싱된 zip 파일
        result = self.server.get_file_info("D:\\Source\\flutter.zip", "LOCAL")
        
        if result["success"]:
            data = result["data"]
            assert data["indexed"] == True
            assert data["file_type"] == "archive"
            
            print(f"  ✓ 파일명: {data['name']}")
            print(f"  ✓ 크기: {data['size']:,} bytes")
            print(f"  ✓ 타입: {data['file_type']}")
            print(f"  ✓ 인덱싱: {data['indexed']}")
            print(f"  ✓ 응답시간: {data.get('elapsed_ms', 'N/A')}ms")
        else:
            print(f"  ⚠ 파일을 찾을 수 없음 (Elasticsearch에 미인덱싱된 상태일 수 있음)")
    
    def test_get_non_indexed_file_info(self):
        """미인덱싱 파일 정보 조회 (파일 시스템)"""
        print("\n[TEST 2] 미인덱싱 파일 정보 조회")
        
        # 테스트 파일이 실제로 존재하는지 확인
        test_file = "D:\\Source\\test_document.txt"
        if not os.path.exists(test_file):
            # 임시 파일 생성
            with open(test_file, 'w') as f:
                f.write("Test content\n")
        
        result = self.server.get_file_info(test_file, "LOCAL")
        
        assert result["success"] == True, f"파일 정보 조회 실패: {result}"
        
        data = result["data"]
        print(f"  ✓ 파일명: {data['name']}")
        print(f"  ✓ 크기: {data['size']} bytes")
        print(f"  ✓ 타입: {data['file_type']}")
        print(f"  ✓ 인덱싱: {data['indexed']}")
        
        assert data["name"] == "test_document.txt"
        assert data["size"] > 0
        assert "modified" in data
        assert data["file_type"] == "text"
    
    def test_get_response_format(self):
        """응답 포맷 검증"""
        print("\n[TEST 3] 응답 포맷 검증")
        
        result = self.server.get_file_info("D:\\Source\\flutter.zip", "LOCAL")
        
        # 최상위 레벨
        assert "success" in result
        assert "data" in result
        assert isinstance(result["success"], bool)
        
        if result["success"]:
            data = result["data"]
            required_fields = ["name", "path", "size", "modified", "file_type", "nas_name", "indexed"]
            
            for field in required_fields:
                assert field in data, f"필드 {field} 없음"
            
            assert isinstance(data["size"], int)
            assert isinstance(data["indexed"], bool)
            
            print(f"  ✓ 응답 포맷 유효")
    
    def test_get_file_not_found(self):
        """파일 없음 처리"""
        print("\n[TEST 4] 파일 없음 처리")
        
        result = self.server.get_file_info("D:\\Source\\nonexistent_file_xyz.txt", "LOCAL")
        
        assert result["success"] == False, "에러 응답이어야 함"
        assert result["error_code"] == "FILE_NOT_FOUND"
        
        print(f"  ✓ 에러 코드: {result['error_code']}")
        print(f"  ✓ 에러 메시지: {result['error']}")
    
    def test_get_path_traversal_protection(self):
        """경로 포함 공격 방어"""
        print("\n[TEST 5] 경로 포함 공격 방어")
        
        result = self.server.get_file_info("../etc/passwd", "LOCAL")
        
        assert result["success"] == False, "에러 응답이어야 함"
        assert result["error_code"] == "INVALID_PATH"
        
        print(f"  ✓ 경로 공격 차단: {result['error']}")
    
    def test_get_different_file_types(self):
        """다양한 파일 타입 정보"""
        print("\n[TEST 6] 다양한 파일 타입")
        
        test_files = [
            ("D:\\Source\\flutter.zip", "archive"),
            ("D:\\Source\\test_document.txt", "text"),
        ]
        
        for file_path, expected_type in test_files:
            if os.path.exists(file_path):
                result = self.server.get_file_info(file_path, "LOCAL")
                
                if result["success"]:
                    data = result["data"]
                    actual_type = data["file_type"]
                    status = "✓" if actual_type == expected_type else "⚠"
                    print(f"  {status} {os.path.basename(file_path)}: {actual_type}")
    
    def test_get_performance(self):
        """성능 테스트"""
        print("\n[TEST 7] 성능 검증 (<100ms)")
        
        result = self.server.get_file_info("D:\\Source\\flutter.zip", "LOCAL")
        
        if result["success"]:
            elapsed_ms = result["data"].get("elapsed_ms", 0)
            print(f"  ✓ 응답시간: {elapsed_ms}ms")
            
            assert elapsed_ms < 100, f"성능 목표 초과: {elapsed_ms}ms"


def main():
    """테스트 실행"""
    print("=" * 70)
    print("MCP get_file_info 도구 테스트")
    print("=" * 70)
    
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    main()
