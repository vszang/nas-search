"""
Elasticsearch 기반 파일 검색 모듈
다양한 검색 옵션을 통한 고성능 파일 검색
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from elasticsearch import Elasticsearch

from .config import ELASTICSEARCH
from .crawler import FileType


logger = logging.getLogger(__name__)


class FileSearcher:
    """
    Elasticsearch 기반 파일 검색
    
    파일명, 콘텐츠, 메타데이터를 기반으로 하는
    다양한 검색 쿼리 제공
    """
    
    def __init__(self):
        try:
            # Elasticsearch 클라이언트 초기화 (v9.x 호환)
            self.client = Elasticsearch([f"http://{ELASTICSEARCH.host}:{ELASTICSEARCH.port}"])
            
            logger.info("Elasticsearch search client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize search client: {str(e)}")
            raise
    
    def search_by_name(
        self,
        query: str,
        file_type: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        파일명으로 검색 (퍼지 매칭)
        
        Args:
            query: 검색 쿼리
            file_type: 파일 타입 필터 (선택사항)
            max_results: 최대 결과 수
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            q = {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "name": {
                                    "query": query,
                                    "fuzziness": "AUTO"
                                }
                            }
                        }
                    ]
                }
            }
            
            # 파일 타입 필터 추가
            if file_type:
                q["bool"]["filter"] = {
                    "term": {"file_type": file_type}
                }
            
            response = self.client.search(
                index=ELASTICSEARCH.index_name,
                query=q,
                size=max_results
            )
            
            return self._format_results(response)
        except Exception as e:
            logger.error(f"Search by name failed: {str(e)}")
            return []
    
    def search_by_content(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        파일 콘텐츠로 검색 (전문검색)
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            response = self.client.search(
                index=ELASTICSEARCH.index_name,
                query={
                    "match": {
                        "content": {
                            "query": query,
                            "fuzziness": "AUTO"
                        }
                    }
                },
                size=max_results
            )
            
            return self._format_results(response)
        except Exception as e:
            logger.error(f"Search by content failed: {str(e)}")
            return []
    
    def search_advanced(
        self,
        name: Optional[str] = None,
        content: Optional[str] = None,
        file_type: Optional[str] = None,
        nas_name: Optional[str] = None,
        min_size: int = 0,
        max_size: int = -1,
        days_modified: int = 365,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        고급 검색 (다중 조건)
        
        Args:
            name: 파일명 검색
            content: 콘텐츠 검색
            file_type: 파일 타입
            nas_name: NAS 이름
            min_size: 최소 파일 크기 (바이트)
            max_size: 최대 파일 크기 (바이트, -1=무제한)
            days_modified: 수정 일수 제한 (기본 365일)
            max_results: 최대 결과 수
        
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            must_clauses = []
            filter_clauses = []
            
            # 파일명 검색
            if name:
                must_clauses.append({
                    "match": {
                        "name": {
                            "query": name,
                            "fuzziness": "AUTO"
                        }
                    }
                })
            
            # 콘텐츠 검색
            if content:
                must_clauses.append({
                    "match": {
                        "content": {
                            "query": content,
                            "fuzziness": "AUTO"
                        }
                    }
                })
            
            # 파일 타입 필터
            if file_type:
                filter_clauses.append({
                    "term": {"file_type": file_type}
                })
            
            # NAS 필터
            if nas_name:
                filter_clauses.append({
                    "term": {"nas_name": nas_name}
                })
            
            # 파일 크기 필터
            size_range = {"gte": min_size}
            if max_size > 0:
                size_range["lte"] = max_size
            
            filter_clauses.append({
                "range": {"size": size_range}
            })
            
            # 쿼리 구성
            if not must_clauses and not filter_clauses:
                # 조건이 없으면 전체 검색
                query = {"match_all": {}}
            elif must_clauses and filter_clauses:
                # 조건이 모두 있는 경우
                query = {
                    "bool": {
                        "must": must_clauses,
                        "filter": filter_clauses
                    }
                }
            elif filter_clauses:
                # 필터만 있는 경우 (항상 true를 must에 추가)
                query = {
                    "bool": {
                        "must": {"match_all": {}},
                        "filter": filter_clauses
                    }
                }
            else:
                # must만 있는 경우
                query = {
                    "bool": {
                        "must": must_clauses
                    }
                }
            
            response = self.client.search(
                index=ELASTICSEARCH.index_name,
                query=query,
                size=max_results
            )
            
            return self._format_results(response)
        except Exception as e:
            logger.error(f"Advanced search failed: {str(e)}")
            return []
    
    def search_by_keyword(
        self,
        query: str,
        file_type: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        파일명 + 내용 통합 검색 (OR 조건)

        Args:
            query: 검색 키워드
            file_type: 파일 타입 필터 (선택사항)
            max_results: 최대 결과 수

        Returns:
            List[Dict]: 검색 결과
        """
        try:
            should_clauses = [
                {"match": {"name":    {"query": query, "fuzziness": "AUTO", "boost": 2}}},
                {"match": {"content": {"query": query, "fuzziness": "AUTO"}}},
            ]

            q: Dict[str, Any] = {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1,
                }
            }

            if file_type:
                q["bool"]["filter"] = {"term": {"file_type": file_type}}

            response = self.client.search(
                index=ELASTICSEARCH.index_name,
                query=q,
                size=max_results
            )

            return self._format_results(response)
        except Exception as e:
            logger.error(f"Keyword search failed: {str(e)}")
            return []

    def _format_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Elasticsearch 응답을 표준 형식으로 변환
        
        Args:
            response: Elasticsearch 검색 응답
        
        Returns:
            List[Dict]: 포맷된 결과 리스트
        """
        results = []
        
        try:
            for hit in response.get("hits", {}).get("hits", []):
                source = hit["_source"]
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "path": source.get("path"),
                    "name": source.get("name"),
                    "size": source.get("size"),
                    "modified": source.get("modified"),
                    "file_type": source.get("file_type"),
                    "nas_name": source.get("nas_name"),
                    "preview": source.get("content", "")[:200]  # 미리보기 (처음 200자)
                })
        except Exception as e:
            logger.error(f"Failed to format results: {str(e)}")
        
        return results
