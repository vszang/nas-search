"""
MCP 서버의 search_files 도구 테스트
"""

import sys
import os
import time
import pytest
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server import NASSearchMCPServer
from src.config import Config


class TestSearchFiles:
    """search_files 도구 테스트"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        Config.validate()
        cls.server = NASSearchMCPServer()
        
        # Elasticsearch에 이미 인덱싱된 데이터 확인
        cls.total_files = 12  # test_integration.py에서 인덱싱된 파일 수
    
    def test_search_simple_query(self):
        """간단한 검색: 파일명 포함 검색"""
        print("\n[TEST 1] 간단한 검색: 'zip' 파일 찾기")
        
        result = self.server.search_files("zip", max_results=50)
        
        assert result["success"] == True, f"검색 실패: {result}"
        assert "data" in result, "응답에 data 필드 없음"
        
        data = result["data"]
        assert "files" in data, "응답에 files 필드 없음"
        assert "total_count" in data, "응답에 total_count 필드 없음"
        assert "elapsed_ms" in data, "응답에 elapsed_ms 필드 없음"
        
        files = data["files"]
        total_count = data["total_count"]
        elapsed_ms = data["elapsed_ms"]
        
        print(f"  ✓ 검색 성공: {total_count}개 파일 발견")
        print(f"  ✓ 소요시간: {elapsed_ms}ms")
        
        # 결과 검증
        assert total_count > 0, f"zip 파일이 0개? (기대: 2개, 실제: {total_count})"
        assert total_count == len(files), f"total_count({total_count})와 파일 개수({len(files)})가 불일치"
        
        # 각 파일의 필드 검증
        for file_obj in files:
            assert "name" in file_obj, "파일 객체에 name 필드 없음"
            assert "path" in file_obj, "파일 객체에 path 필드 없음"
            assert "size" in file_obj, "파일 객체에 size 필드 없음"
            assert "modified" in file_obj, "파일 객체에 modified 필드 없음"
            assert "file_type" in file_obj, "파일 객체에 file_type 필드 없음"
            assert "nas_name" in file_obj, "파일 객체에 nas_name 필드 없음"
            assert "score" in file_obj, "파일 객체에 score 필드 없음"
            
            print(f"  ✓ {file_obj['name']} ({file_obj['size']} bytes, score={file_obj['score']})")
        
        # 검색 결과 기대값
        assert 1 <= total_count <= 5, f"zip 검색 결과가 예상과 다름 (expected 1-5, got {total_count})"
    
    def test_search_with_file_type_filter(self):
        """필터 테스트: 파일 타입 필터로 검색"""
        print("\n[TEST 2] 필터 검색: archive 타입 파일 찾기")
        
        result = self.server.search_files("", file_type="archive", max_results=50)
        
        assert result["success"] == True, f"필터 검색 실패: {result}"
        
        data = result["data"]
        files = data["files"]
        total_count = data["total_count"]
        
        print(f"  ✓ Archive 파일 발견: {total_count}개")
        
        # 모든 파일이 archive 타입인지 확인
        for file_obj in files:
            assert file_obj["file_type"] == "archive", \
                f"파일 타입 필터 실패: {file_obj['name']}은 {file_obj['file_type']}"
        
        if files:
            print(f"  ✓ 파일 샘플:")
            for file_obj in files[:3]:
                print(f"    - {file_obj['name']} ({file_obj['size']} bytes)")
    
    def test_search_combined_query_and_filter(self):
        """복합 검색: 쿼리 + 필터"""
        print("\n[TEST 3] 복합 검색: 'node' 검색 + archive 필터")
        
        result = self.server.search_files("node", file_type="archive", max_results=50)
        
        assert result["success"] == True, f"복합 검색 실패: {result}"
        
        data = result["data"]
        files = data["files"]
        total_count = data["total_count"]
        
        print(f"  ✓ 복합 검색 결과: {total_count}개 파일")
        
        for file_obj in files:
            assert file_obj["file_type"] == "archive", "필터 검증 실패"
            print(f"  ✓ {file_obj['name']}")
    
    def test_search_empty_result(self):
        """빈 결과 테스트: 없는 파일 검색"""
        print("\n[TEST 4] 빈 결과 처리: 'nonexistent_xyz_12345' 검색")
        
        result = self.server.search_files("nonexistent_xyz_12345", max_results=50)
        
        assert result["success"] == True, f"검색 실패: {result}"
        
        data = result["data"]
        files = data["files"]
        total_count = data["total_count"]
        
        print(f"  ✓ 예상대로 0개 결과: {total_count}개")
        
        assert total_count == 0, f"기대: 0, 실제: {total_count}"
        assert len(files) == 0, "빈 파일 리스트 기대"
    
    def test_search_performance(self):
        """성능 테스트: 응답시간 100ms 이내"""
        print("\n[TEST 5] 성능 검증: 응답시간 < 100ms")
        
        result = self.server.search_files("zip", max_results=50)
        
        assert result["success"] == True, f"검색 실패: {result}"
        
        elapsed_ms = result["data"]["elapsed_ms"]
        
        print(f"  ✓ 응답시간: {elapsed_ms}ms")
        
        assert elapsed_ms < 100, f"응답시간이 목표 100ms를 초과: {elapsed_ms}ms"
    
    def test_search_max_results(self):
        """max_results 파라미터 테스트"""
        print("\n[TEST 6] max_results 파라미터 테스트")
        
        # max_results 제한 없음
        result1 = self.server.search_files("", max_results=100)
        count1 = len(result1["data"]["files"])
        
        # max_results 5개 제한
        result2 = self.server.search_files("", max_results=5)
        count2 = len(result2["data"]["files"])
        
        print(f"  ✓ max_results=100: {count1}개")
        print(f"  ✓ max_results=5: {count2}개")
        
        assert count2 <= count1, "max_results 제한이 작동하지 않음"
        assert count2 <= 5, f"max_results=5인데 {count2}개 반환됨"
    
    def test_search_response_format(self):
        """응답 포맷 검증"""
        print("\n[TEST 7] 응답 포맷 검증")
        
        result = self.server.search_files("archive", max_results=1)
        
        # 최상위 레벨
        assert "success" in result, "success 필드 없음"
        assert "data" in result, "data 필드 없음"
        assert isinstance(result["success"], bool), "success는 boolean이어야 함"
        
        # data 필드
        data = result["data"]
        assert "files" in data, "data.files 필드 없음"
        assert "total_count" in data, "data.total_count 필드 없음"
        assert "elapsed_ms" in data, "data.elapsed_ms 필드 없음"
        
        assert isinstance(data["files"], list), "files는 리스트여야 함"
        assert isinstance(data["total_count"], int), "total_count는 int여야 함"
        assert isinstance(data["elapsed_ms"], (int, float)), "elapsed_ms는 숫자여야 함"
        
        print(f"  ✓ 응답 포맷 유효")
    
    def test_search_score_sorting(self):
        """검색 결과 스코어 정렬"""
        print("\n[TEST 8] 검색 결과 스코어 정렬 검증")
        
        result = self.server.search_files("zip", max_results=10)
        
        if result["data"]["total_count"] > 1:
            files = result["data"]["files"]
            scores = [f["score"] for f in files]
            
            # 스코어가 감소하는지 확인 (정렬됨)
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], f"스코어 정렬 실패: {scores}"
            
            print(f"  ✓ 스코어 정렬 확인: {scores[:3]}...")
    
    def test_search_all_file_types(self):
        """모든 파일 타입으로 검색"""
        print("\n[TEST 9] 모든 파일 타입 필터 테스트")
        
        file_types = ["document", "text", "image", "video", "audio", "archive", "code", "other"]
        
        for file_type in file_types:
            result = self.server.search_files("", file_type=file_type, max_results=50)
            
            assert result["success"] == True, f"파일타입 {file_type} 검색 실패"
            
            count = result["data"]["total_count"]
            print(f"  ✓ {file_type}: {count}개")
            
            # 반환된 모든 파일이 해당 타입인지 확인
            for file_obj in result["data"]["files"]:
                assert file_obj["file_type"] == file_type, \
                    f"파일타입 불일치: {file_obj['file_type']} != {file_type}"


class TestSearchFilesErrorHandling:
    """search_files 에러 처리 테스트"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        Config.validate()
        cls.server = NASSearchMCPServer()
    
    def test_search_invalid_file_type(self):
        """유효하지 않은 파일 타입 처리"""
        print("\n[TEST E1] 유효하지 않은 파일 타입")
        
        # 유효하지 않은 file_type은 필터로 작동 (결과 0개)
        result = self.server.search_files("", file_type="invalid_type", max_results=50)
        
        # Elasticsearch는 존재하지 않는 필터에 대해 0개 결과 반환
        assert result["success"] == True, "에러 응답이어야 함"
        assert result["data"]["total_count"] == 0, "유효하지 않은 타입은 0개 결과"
        
        print(f"  ✓ 유효하지 않은 파일타입은 0개 결과 반환")
    
    def test_search_empty_query(self):
        """빈 쿼리 처리"""
        print("\n[TEST E2] 빈 쿼리 (전체 파일 조회)")
        
        result = self.server.search_files("", max_results=50)
        
        assert result["success"] == True, f"빈 쿼리 검색 실패: {result}"
        
        # 빈 쿼리는 전체 파일 반환
        count = result["data"]["total_count"]
        print(f"  ✓ 빈 쿼리: {count}개 파일 (전체)")
        
        assert count >= 0, f"음수 개수: {count}"
    
    def test_search_special_characters(self):
        """특수문자가 포함된 쿼리"""
        print("\n[TEST E3] 특수문자 쿼리")
        
        special_queries = [
            "test@file",
            "file#1",
            "test$",
            "file&name",
            "test/path",
            "file\\name"
        ]
        
        for query in special_queries:
            result = self.server.search_files(query, max_results=10)
            
            # 에러 없이 완료되어야 함
            assert "success" in result, f"쿼리 '{query}' 처리 실패"
            print(f"  ✓ '{query}' 처리 완료")


def main():
    """테스트 실행"""
    print("=" * 70)
    print("MCP search_files 도구 테스트")
    print("=" * 70)
    
    # pytest로 테스트 실행
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    main()
