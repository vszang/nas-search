"""
Elasticsearch 인덱서 모듈
파일 메타데이터 및 콘텐츠를 Elasticsearch에 인덱싱
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from .config import ELASTICSEARCH, Config
from .crawler import FileMetadata


logger = logging.getLogger(__name__)


class FileIndexer:
    """
    Elasticsearch 기반 파일 인덱싱
    
    파일 메타데이터를 Elasticsearch에 저장하고
    전문검색(Full-text search) 기능 제공
    """
    
    def __init__(self):
        try:
            # Elasticsearch 클라이언트 초기화 (v9.x 호환)
            self.client = Elasticsearch([f"http://{ELASTICSEARCH.host}:{ELASTICSEARCH.port}"])
            
            logger.info(f"Elasticsearch connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {str(e)}")
            raise
    
    def create_index(self) -> bool:
        """
        인덱스 생성 (매핑 포함)
        
        Returns:
            bool: 성공 여부
        """
        index_name = ELASTICSEARCH.index_name
        
        # 인덱스 매핑 정의
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "korean_analyzer": {
                            "type": "standard",
                            "stopwords": "_korean_"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "name": {
                        "type": "text",
                        "analyzer": "korean_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "korean_analyzer"
                    },
                    "size": {
                        "type": "long"
                    },
                    "modified": {
                        "type": "date"
                    },
                    "file_type": {
                        "type": "keyword"
                    },
                    "nas_name": {
                        "type": "keyword"
                    },
                    "indexed_at": {
                        "type": "date"
                    }
                }
            }
        }
        
        try:
            # 기존 인덱스 삭제 (테스트용)
            if self.client.indices.exists(index=index_name):
                logger.info(f"Deleting existing index: {index_name}")
                self.client.indices.delete(index=index_name)
            
            # 새 인덱스 생성
            self.client.indices.create(index=index_name, body=mapping)
            logger.info(f"Index created: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {str(e)}")
            return False
    
    def index_file(self, file_metadata: FileMetadata, content: str = "") -> bool:
        """
        개별 파일 인덱싱
        
        Args:
            file_metadata: 파일 메타데이터
            content: 파일 콘텐츠 (전문검색용)
        
        Returns:
            bool: 성공 여부
        """
        try:
            doc = {
                "path": file_metadata.path,
                "name": file_metadata.name,
                "content": content,
                "size": file_metadata.size,
                "modified": file_metadata.modified,
                "file_type": file_metadata.file_type.value,
                "nas_name": file_metadata.nas_name,
                "indexed_at": datetime.now()
            }
            
            self.client.index(
                index=ELASTICSEARCH.index_name,
                document=doc
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index file {file_metadata.path}: {str(e)}")
            return False
    
    def batch_index_files(self, files: List[tuple]) -> int:
        """
        배치 인덱싱 (성능 최적화)
        
        Args:
            files: (FileMetadata, 콘텐츠) 튜플 리스트
        
        Returns:
            int: 성공적으로 인덱싱된 파일 수
        """
        success_count = 0
        
        for file_metadata, content in files:
            try:
                doc = {
                    "path": file_metadata.path,
                    "name": file_metadata.name,
                    "content": content,
                    "size": file_metadata.size,
                    "modified": file_metadata.modified,
                    "file_type": file_metadata.file_type.value,
                    "nas_name": file_metadata.nas_name,
                    "indexed_at": datetime.now()
                }
                
                self.client.index(
                    index=ELASTICSEARCH.index_name,
                    document=doc
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to index file {file_metadata.path}: {str(e)}")
        
        # 인덱스 refresh (즉시 검색 가능하도록)
        try:
            self.client.indices.refresh(index=ELASTICSEARCH.index_name)
        except Exception as e:
            logger.warning(f"Failed to refresh index: {str(e)}")
        
        logger.info(f"Batch indexed {success_count} files")
        return success_count
    
    def delete_index(self) -> bool:
        """
        인덱스 삭제 (테스트용)
        
        Returns:
            bool: 성공 여부
        """
        try:
            self.client.indices.delete(index=ELASTICSEARCH.index_name)
            logger.info(f"Index deleted: {ELASTICSEARCH.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index: {str(e)}")
            return False
