"""
RAG (Retrieval Augmented Generation) 시스템
벡터 검색을 통한 의미 기반 문서 검색 및 Claude AI 기반 답변
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    from elasticsearch import Elasticsearch
except ImportError:
    logging.warning("Required packages not installed. Install sentence-transformers and elasticsearch.")

logger = logging.getLogger(__name__)


class RAGSystem:
    """
    RAG 시스템
    
    벡터 임베딩을 통해 의미 기반으로 문서를 검색하고,
    검색된 문서의 내용을 Claude AI에 제공하여 답변 생성
    """
    
    def __init__(self, es_host: str = "localhost", es_port: int = 9200):
        """RAG 시스템 초기화"""
        try:
            # Elasticsearch 연결 (최신 버전 호환)
            es_url = f"http://{es_host}:{es_port}"
            self.es = Elasticsearch([es_url])
            
            # 연결 테스트
            info = self.es.info()
            logger.info(f"Elasticsearch 연결 성공: {info.get('version', {}).get('number', 'unknown')}")
            
            # 벡터 임베딩 모델 로드
            # 작은 모델 사용 (빠른 응답)
            logger.info("벡터 임베딩 모델 로드 중...")
            self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("벡터 임베딩 모델 로드 완료")
            
            self.index_name = "nas_documents"
            
            logger.info("RAG 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"RAG 시스템 초기화 실패: {str(e)}")
            raise
    
    def create_index(self):
        """Elasticsearch 벡터 인덱스 생성"""
        try:
            # 기존 인덱스 삭제
            if self.es.indices.exists(index=self.index_name):
                self.es.indices.delete(index=self.index_name)
                logger.info(f"기존 인덱스 삭제: {self.index_name}")
            
            # 새 인덱스 생성 (벡터 필드 포함)
            index_body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "file_path": {"type": "keyword"},
                        "file_name": {"type": "text"},
                        "content": {"type": "text"},
                        "content_vector": {
                            "type": "dense_vector",
                            "dims": 384,  # MiniLM-L6 임베딩 크기
                            "index": True,
                            "similarity": "cosine"
                        },
                        "file_type": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "modified_date": {"type": "date"},
                        "nas_name": {"type": "keyword"}
                    }
                }
            }
            
            self.es.indices.create(index=self.index_name, body=index_body)
            logger.info(f"인덱스 생성 완료: {self.index_name}")
            
        except Exception as e:
            logger.error(f"인덱스 생성 실패: {str(e)}")
            raise
    
    def index_document(self, file_path: str, content: str, 
                      file_name: str = "", file_type: str = "", 
                      file_size: int = 0, modified_date: str = "",
                      nas_name: str = "") -> bool:
        """문서를 벡터와 함께 인덱싱"""
        try:
            # 내용을 벡터로 변환
            content_vector = self.embedder.encode(content).tolist()
            
            # 문서 생성
            doc = {
                "file_path": file_path,
                "file_name": file_name or file_path.split('/')[-1],
                "content": content[:5000],  # 처음 5000자만 인덱싱
                "content_vector": content_vector,
                "file_type": file_type,
                "file_size": file_size,
                "nas_name": nas_name,
                "indexed_at": datetime.now().isoformat()
            }
            if modified_date:
                doc["modified_date"] = modified_date
            
            # Elasticsearch에 인덱싱
            self.es.index(index=self.index_name, document=doc)
            
            logger.info(f"문서 인덱싱: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"문서 인덱싱 실패 ({file_path}): {str(e)}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """의미 기반 벡터 검색"""
        try:
            # 쿼리를 벡터로 변환
            query_vector = self.embedder.encode(query).tolist()
            
            # Elasticsearch 벡터 검색
            search_body = {
                "size": top_k,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                            "params": {
                                "query_vector": query_vector
                            }
                        }
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
            
            logger.info(f"검색 완료: '{query}' → {len(documents)}개 문서")
            return documents
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {str(e)}")
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
                    "content": doc.get("content", ""),
                    "score": doc.get("score", 0),
                    "file_type": doc.get("file_type", ""),
                    "modified_date": doc.get("modified_date", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"상세 검색 실패: {str(e)}")
            return []


# 전역 RAG 시스템
rag_system = None


def get_rag_system() -> Optional[RAGSystem]:
    """RAG 시스템 인스턴스 (싱글톤)"""
    global rag_system
    if rag_system is None:
        try:
            rag_system = RAGSystem()
        except Exception as e:
            logger.error(f"RAG 시스템 초기화 실패: {str(e)}")
            return None
    return rag_system
