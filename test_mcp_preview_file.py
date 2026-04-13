"""
MCP 서버의 preview_file 도구 테스트
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


class TestPreviewFile:
    """preview_file 도구 테스트"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        Config.validate()
        cls.server = NASSearchMCPServer()
        
        # 테스트 파일들 생성
        cls.test_text_file = "D:\\Source\\preview_test_text.txt"
        cls.test_json_file = "D:\\Source\\preview_test_config.json"
        cls.test_python_file = "D:\\Source\\preview_test_script.py"
        cls.test_large_file = "D:\\Source\\preview_test_large.txt"
        
        # 텍스트 파일
        if not os.path.exists(cls.test_text_file):
            with open(cls.test_text_file, 'w', encoding='utf-8') as f:
                f.write("Line 1: Test content\n")
                f.write("Line 2: 한글 테스트\n")
                f.write("Line 3: Multiple lines\n" * 20)
        
        # JSON 파일
        if not os.path.exists(cls.test_json_file):
            with open(cls.test_json_file, 'w', encoding='utf-8') as f:
                f.write('{"name": "test", "value": 123, "items": ["a", "b", "c"]}\n')
        
        # Python 파일
        if not os.path.exists(cls.test_python_file):
            with open(cls.test_python_file, 'w', encoding='utf-8') as f:
                f.write("#!/usr/bin/env python3\n")
                f.write("# Test script\n")
                f.write("print('Hello, World!')\n")
        
        # 큰 파일 (6MB)
        if not os.path.exists(cls.test_large_file):
            with open(cls.test_large_file, 'w') as f:
                f.write("x" * (6 * 1024 * 1024))
    
    def test_preview_text_file(self):
        """텍스트 파일 미리보기"""
        print("\n[TEST 1] 텍스트 파일 미리보기")
        
        result = self.server.preview_file(self.test_text_file)
        
        assert result["success"] == True, f"미리보기 실패: {result}"
        
        data = result["data"]
        assert data["is_text"] == True
        assert len(data["content"]) > 0
        
        print(f"  ✓ 파일명: {data['name']}")
        print(f"  ✓ 크기: {data['size']} bytes")
        print(f"  ✓ 인코딩: {data['encoding']}")
        print(f"  ✓ 라인 수: {data['lines']}")
        print(f"  ✓ 잘림: {data['truncated']}")
        print(f"  ✓ 응답시간: {data.get('elapsed_ms', 'N/A')}ms")
        print(f"  ✓ 콘텐츠 미리보기:\n{data['content'][:100]}...")
    
    def test_preview_json_file(self):
        """JSON 파일 미리보기"""
        print("\n[TEST 2] JSON 파일 미리보기")
        
        result = self.server.preview_file(self.test_json_file, max_bytes=2048)
        
        if result["success"]:
            data = result["data"]
            print(f"  ✓ JSON 파일 (크기: {data['size']} bytes)")
            print(f"  ✓ 콘텐츠:\n{data['content']}")
        else:
            print(f"  ⚠ 미리보기 실패: {result['error']}")
    
    def test_preview_python_file(self):
        """Python 파일 미리보기"""
        print("\n[TEST 3] Python 파일 미리보기")
        
        result = self.server.preview_file(self.test_python_file)
        
        if result["success"]:
            data = result["data"]
            assert "python" in data["content"].lower() or "print" in data["content"]
            print(f"  ✓ Python 파일 (라인: {data['lines']})")
            print(f"  ✓ 콘텐츠:\n{data['content']}")
        else:
            print(f"  ⚠ 미리보기 실패: {result['error']}")
    
    def test_preview_large_file_truncation(self):
        """큰 파일 자르기 (5MB > 1KB)"""
        print("\n[TEST 4] 큰 파일 자르기 테스트")
        
        result = self.server.preview_file(self.test_large_file, max_bytes=1024)
        
        assert result["success"] == True, f"미리보기 실패: {result}"
        
        data = result["data"]
        print(f"  ✓ 파일 크기: {data['size']:,} bytes")
        print(f"  ✓ 읽은 크기: {len(data['content'])} bytes")
        print(f"  ✓ 잘림 여부: {data['truncated']}")
        
        assert data["truncated"] == True, "큰 파일은 잘린 것으로 표시되어야 함"
        assert len(data["content"]) <= 1024, "요청한 크기를 초과하여 읽음"
    
    def test_preview_response_format(self):
        """응답 포맷 검증"""
        print("\n[TEST 5] 응답 포맷 검증")
        
        result = self.server.preview_file(self.test_text_file)
        
        # 최상위 레벨
        assert "success" in result
        assert "data" in result
        
        if result["success"]:
            data = result["data"]
            required_fields = ["name", "content", "is_text", "truncated", "size", "encoding", "lines"]
            
            for field in required_fields:
                assert field in data, f"필드 {field} 없음"
            
            assert isinstance(data["is_text"], bool)
            assert isinstance(data["truncated"], bool)
            assert isinstance(data["size"], int)
            assert isinstance(data["lines"], int)
            
            print(f"  ✓ 응답 포맷 유효")
    
    def test_preview_binary_file_rejection(self):
        """바이너리 파일 거부 (ZIP)"""
        print("\n[TEST 6] 바이너리 파일 거부")
        
        # ZIP 파일 (바이너리)
        result = self.server.preview_file("D:\\Source\\flutter.zip")
        
        assert result["success"] == False, "바이너리 파일 미리보기는 거부되어야 함"
        assert result["error_code"] == "UNSUPPORTED_TYPE"
        
        print(f"  ✓ 에러 코드: {result['error_code']}")
        print(f"  ✓ 에러 메시지: {result['error']}")
    
    def test_preview_file_not_found(self):
        """파일 없음 처리"""
        print("\n[TEST 7] 파일 없음 처리")
        
        result = self.server.preview_file("D:\\Source\\nonexistent_xyz.txt")
        
        assert result["success"] == False, "에러 응답이어야 함"
        assert result["error_code"] == "FILE_NOT_FOUND"
        
        print(f"  ✓ 에러 코드: {result['error_code']}")
    
    def test_preview_path_traversal_protection(self):
        """경로 포함 공격 방어"""
        print("\n[TEST 8] 경로 포함 공격 방어")
        
        result = self.server.preview_file("../etc/passwd")
        
        assert result["success"] == False, "에러 응답이어야 함"
        assert result["error_code"] == "INVALID_PATH"
        
        print(f"  ✓ 경로 공격 차단: {result['error']}")
    
    def test_preview_encoding_detection(self):
        """인코딩 감지"""
        print("\n[TEST 9] 인코딩 감지 테스트")
        
        # UTF-8 파일
        result_utf8 = self.server.preview_file(self.test_text_file)
        
        if result_utf8["success"]:
            encoding = result_utf8["data"]["encoding"]
            print(f"  ✓ UTF-8 파일 인코딩: {encoding}")
            assert encoding in ["utf-8", "utf8", "UTF-8"], f"예상과 다른 인코딩: {encoding}"
    
    def test_preview_different_max_bytes(self):
        """다양한 max_bytes 테스트"""
        print("\n[TEST 10] max_bytes 파라미터 테스트")
        
        max_bytes_list = [100, 512, 1024, 2048]
        
        for max_bytes in max_bytes_list:
            result = self.server.preview_file(self.test_text_file, max_bytes=max_bytes)
            
            if result["success"]:
                actual_size = len(result["data"]["content"])
                print(f"  ✓ max_bytes={max_bytes}: {actual_size} bytes 읽음")
                
                assert actual_size <= max_bytes, f"요청한 크기 초과: {actual_size} > {max_bytes}"
    
    def test_preview_performance(self):
        """성능 테스트"""
        print("\n[TEST 11] 성능 검증 (<100ms)")
        
        result = self.server.preview_file(self.test_text_file)
        
        if result["success"]:
            elapsed_ms = result["data"].get("elapsed_ms", 0)
            print(f"  ✓ 응답시간: {elapsed_ms}ms")
            
            assert elapsed_ms < 100, f"성능 목표 초과: {elapsed_ms}ms"
    
    def test_preview_supported_text_extensions(self):
        """지원되는 텍스트 확장자 테스트"""
        print("\n[TEST 12] 지원되는 텍스트 확장자")
        
        # _is_text_file 메서드 테스트
        supported_files = [
            "test.txt",
            "test.log",
            "test.md",
            "test.json",
            "test.py",
            "test.js",
            "test.html",
            "test.csv",
            "test.xml"
        ]
        
        for filename in supported_files:
            is_text = self.server._is_text_file(filename)
            status = "✓" if is_text else "✗"
            print(f"  {status} {filename}: {is_text}")


def main():
    """테스트 실행"""
    print("=" * 70)
    print("MCP preview_file 도구 테스트")
    print("=" * 70)
    
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    main()
