"""
RAG (Retrieval Augmented Generation) 시스템 - 최적화 버전
벡터 검색을 통한 의미 기반 문서 검색 및 Claude AI 기반 답변
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from functools import lru_cache
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    from elasticsearch import Elasticsearch
except ImportError:
    logging.warning("Required packages not installed. Install sentence-transformers and elasticsearch.")

logger = logging.getLogger(__name__)

# 캐싱 설정
EMBEDDING_CACHE_SIZE = 1000
QUERY_CACHE_SIZE = 100


class RAGSystemOptimized:
    """
    최적화된 RAG 시스템
    
    개선사항:
    1. 임베딩 캐싱 (LRU) - 반복되는 텍스트 재임베딩 방지
    2. 배치 임베딩 처리 - 대량 문서 효율적 처리
    3. 검색 쿼리 최적화 - KNN 벡터 검색 (Elasticsearch 8.0+)
    4. 결과 캐싱 - 최근 검색 결과 메모리 캐싱
    5. 스코어 임계값 - 관련성 낮은 결과 필터링
    """
    
    def __init__(self, es_host: str = "localhost", es_port: int = 9200, use_quantization: bool = False):
        """최적화된 RAG 시스템 초기화
        
        Args:
            es_host: Elasticsearch 호스트
            es_port: Elasticsearch 포트
            use_quantization: 모델 양자화 사용 여부 (메모리 절약, 약간 느림)
        """
        try:
            # Elasticsearch 연결
            es_url = f"http://{es_host}:{es_port}"
            self.es = Elasticsearch([es_url])
            
            # 연결 테스트
            info = self.es.info()
            logger.info(f"✅ Elasticsearch 연결 성공: {info.get('version', {}).get('number', 'unknown')}")
            
            # 벡터 임베딩 모델 로드
            logger.info("📊 벡터 임베딩 모델 로드 중...")
            self.embedder = SentenceTransformer('multilingual-MiniLM-L6-v2')
            
            # 배치 인코딩을위한 설정
            self.embedder.max_seq_length = 256  # 처리 속도 향상
            
            logger.info("✅ 벡터 임베딩 모델 로드 완료")
            
            self.index_name = "nas_documents_v2"
            self.min_score = 0.3  # 관련도 임계값 (0-1 범위)
            
            # 쿼리 결과 캐시
            self._query_cache: Dict[str, List[Dict]] = {}
            self._cache_hits = 0
            self._cache_misses = 0
            
            logger.info("✅ RAG 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ RAG 시스템 초기화 실패: {str(e)}")
            raise
    
    def _hash_text(self, text: str) -> str:
        """텍스트의 해시값 계산 (캐시 키용)"""
        return hashlib.md5(text.encode()).hexdigest()
    
    @lru_cache(maxsize=EMBEDDING_CACHE_SIZE)
    def _encode_text(self, text_hash: str, text: str) -> Tuple[tuple, ...]:
        """텍스트 임베딩 (LRU 캐시 적용)"""
        vector = self.embedder.encode(text, convert_to_tensor=False)
        return tuple(vector)
    
    def encode_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환 (캐싱 포함)"""
        try:
            text_hash = self._hash_text(text)
            vector_tuple = self._encode_text(text_hash, text)
            return list(vector_tuple)
        except Exception as e:
            logger.error(f"❌ 텍스트 임베딩 실패: {str(e)}")
            return []
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """배치 임베딩 처리 (효율적)
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기 (메모리와 속도의 균형)
        
        Returns:
            임베딩 벡터 리스트
        """
        try:
            vectors = self.embedder.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_tensor=False
            )
            return [v.tolist() for v in vectors]
        except Exception as e:
            logger.error(f"❌ 배치 임베딩 실패: {str(e)}")
            return [[] for _ in texts]
    
    def create_index(self):
        """최적화된 벡터 인덱스 생성"""
        try:
            # 기존 인덱스 삭제
            if self.es.indices.exists(index=self.index_name):
                self.es.indices.delete(index=self.index_name)
                logger.info(f"🗑️  기존 인덱스 삭제: {self.index_name}")
            
            # 최적화된 인덱스 설정
            index_body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index": {
                        "knn": True,  # KNN 벡터 검색 활성화
                        "knn.algo_param.ef_construction": 128  # 인덱싱 정확도
                    }
                },
                "mappings": {
                    "properties": {
                        "file_path": {"type": "keyword"},
                        "file_name": {"type": "text", "analyzer": "standard"},
                        "content": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {"keyword": {"type": "keyword"}}
                        },
                        "content_vector": {
                            "type": "dense_vector",
                            "dims": 384,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "content_summary": {"type": "text"},
                        "file_type": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "modified_date": {"type": "date"},
                        "nas_name": {"type": "keyword"},
                        "indexed_at": {"type": "date"}
                    }
                }
            }
            
            self.es.indices.create(index=self.index_name, body=index_body)
            logger.info(f"✅ 최적화된 인덱스 생성: {self.index_name}")
            
        except Exception as e:
            logger.error(f"❌ 인덱스 생성 실패: {str(e)}")
            raise
    
    def index_document(self, file_path: str, content: str, 
                      file_name: str = "", file_type: str = "", 
                      file_size: int = 0, modified_date: str = "",
                      nas_name: str = "") -> bool:
        """특정 문서를 인덱싱"""
        try:
            # 임베딩 생성
            content_vector = self.encode_text(content[:1000])  # 처음 1000자만 사용
            if not content_vector:
                return False
            
            # 문서 생성
            doc = {
                "file_path": file_path,
                "file_name": file_name or file_path.split('/')[-1],
                "content": content[:10000],  # 검색용 내용 (처음 10000자)
                "content_summary": content[:200],  # 요약용
                "content_vector": content_vector,
                "file_type": file_type,
                "file_size": file_size,
                "modified_date": modified_date,
                "nas_name": nas_name,
                "indexed_at": datetime.now().isoformat()
            }
            
            # Elasticsearch에 인덱싱
            self.es.index(index=self.index_name, doc_type="_doc", body=doc)
            return True
            
        except Exception as e:
            logger.error(f"❌ 문서 인덱싱 실패 ({file_path}): {str(e)}")
            return False
    
    def batch_index_documents(self, documents: List[Dict[str, Any]]) -> Tuple[int, int]:
        """배치 인덱싱 (효율적)
        
        Args:
            documents: [
                {
                    "file_path": "...",
                    "content": "...",
                    "file_name": "...",
                    ...
                },
                ...
            ]
        
        Returns:
            (성공한 문서 수, 실패한 문서 수)
        """
        try:
            # 임베딩 배치 처리
            contents = [doc.get("content", "")[:1000] for doc in documents]
            vectors = self.batch_encode(contents, batch_size=32)
            
            success_count = 0
            failure_count = 0
            
            # 벌크 인덱싱
            from elasticsearch.helpers import bulk
            
            actions = []
            for doc, vector in zip(documents, vectors):
                if vector:
                    actions.append({
                        "_index": self.index_name,
                        "_type": "_doc",
                        "_source": {
                            **doc,
                            "content_vector": vector,
                            "indexed_at": datetime.now().isoformat()
                        }
                    })
            
            # 벌크 작업 실행
            for success, info in bulk(self.es, actions, chunk_size=50):
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            
            logger.info(f"📦 배치 인덱싱 완료: {success_count}개 성공, {failure_count}개 실패")
            return success_count, failure_count
            
        except Exception as e:
            logger.error(f"❌ 배치 인덱싱 실패: {str(e)}")
            return 0, len(documents)
    
    def search(self, query: str, top_k: int = 5, min_score: Optional[float] = None) -> List[Dict[str, Any]]:
        """최적화된 의미 기반 벡터 검색"""
        try:
            # 캐시 확인
            cache_key = f"{query}:{top_k}"
            if cache_key in self._query_cache:
                self._cache_hits += 1
                logger.debug(f"💾 캐시 히트: {query}")
                return self._query_cache[cache_key]
            
            self._cache_misses += 1
            
            # 쿼리 임베딩
            query_vector = self.encode_text(query)
            if not query_vector:
                return []
            
            # 최적화된 KNN 검색 쿼리
            search_body = {
                "size": top_k,
                "_source": ["file_path", "file_name", "content_summary", "file_type", "modified_date"],
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                            "params": {"query_vector": query_vector}
                        },
                        "min_score": min_score or self.min_score + 1.0  # 절대값 조정
                    }
                }
            }
            
            results = self.es.search(index=self.index_name, body=search_body)
            
            # 결과 포매팅
            documents = []
            for hit in results['hits']['hits']:
                doc = hit['_source']
                doc['score'] = hit['_score']
                documents.append(doc)
            
            # 캐시에 저장 (최대 100개 쿼리 결과)
            if len(self._query_cache) > QUERY_CACHE_SIZE:
                self._query_cache.pop(next(iter(self._query_cache)))
            self._query_cache[cache_key] = documents
            
            logger.info(f"🔍 검색 완료: '{query}' → {len(documents)}개 문서 (스코어: {[d['score'] for d in documents[:3]]})")
            return documents
            
        except Exception as e:
            logger.error(f"❌ 벡터 검색 실패: {str(e)}")
            return []
    
    def search_with_content(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """검색 후 상세 내용 반환 (Claude 입력용)"""
        try:
            documents = self.search(query, top_k)
            
            # 각 문서의 내용과 경로 반환
            results = []
            for doc in documents:
                results.append({
                    "file_path": doc.get("file_path", ""),
                    "file_name": doc.get("file_name", ""),
                    "content": doc.get("content_summary", ""),
                    "score": doc.get("score", 0),
                    "file_type": doc.get("file_type", ""),
                    "modified_date": doc.get("modified_date", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 상세 검색 실패: {str(e)}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "cached_queries": len(self._query_cache),
            "embedding_cache_size": self._encode_text.cache_info().currsize
        }
    
    def clear_caches(self):
        """모든 캐시 초기화"""
        self._query_cache.clear()
        self._encode_text.cache_clear()
        logger.info("🗑️  모든 캐시 초기화 완료")


# 전역 RAG 시스템
rag_system = None


def get_rag_system() -> Optional[RAGSystemOptimized]:
    """최적화된 RAG 시스템 인스턴스 (싱글톤)"""
    global rag_system
    if rag_system is None:
        try:
            rag_system = RAGSystemOptimized()
        except Exception as e:
            logger.error(f"❌ RAG 시스템 초기화 실패: {str(e)}")
            return None
    return rag_system
