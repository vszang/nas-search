"""
설정 관리 모듈
환경 변수 로딩 및 설정 검증
"""

import os
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv


load_dotenv()


@dataclass
class NASConfig:
    """NAS 연결 설정"""
    host: str
    share: str
    username: str
    password: str
    name: str
    start_path: str = ""  # 크롤링 시작 경로 (비어있으면 공유 루트 전체)


@dataclass
class ElasticsearchConfig:
    """Elasticsearch 설정"""
    host: str = "localhost"
    port: int = 9200
    username: str = "elastic"
    password: str = "changeme"
    index_name: str = "nas_files"
    use_ssl: bool = True


@dataclass
class CrawlerConfig:
    """크롤러 설정"""
    batch_size: int = 100
    thread_count: int = 4
    timeout: int = 30
    retry_count: int = 3
    update_interval: int = 86400  # 24시간


@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"
    log_file: str = "logs/nas_search.log"


class Config:
    """전체 애플리케이션 설정"""
    
    # NAS 설정 동적 로딩
    NAS_CONFIGS: List[NASConfig] = []
    
    @classmethod
    def load_elasticsearch(cls) -> ElasticsearchConfig:
        """Elasticsearch 설정 로드"""
        return ElasticsearchConfig(
            host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
            port=int(os.getenv("ELASTICSEARCH_PORT", "9200")),
            username=os.getenv("ELASTICSEARCH_USERNAME", "elastic"),
            password=os.getenv("ELASTICSEARCH_PASSWORD", "changeme"),
            index_name=os.getenv("ELASTICSEARCH_INDEX_NAME", "nas_files"),
            use_ssl=os.getenv("ELASTICSEARCH_USE_SSL", "true").lower() == "true"
        )
    
    @classmethod
    def load_crawler(cls) -> CrawlerConfig:
        """크롤러 설정 로드"""
        return CrawlerConfig(
            batch_size=int(os.getenv("CRAWLER_BATCH_SIZE", "100")),
            thread_count=int(os.getenv("CRAWLER_THREAD_COUNT", "4")),
            timeout=int(os.getenv("CRAWLER_TIMEOUT", "30")),
            retry_count=int(os.getenv("CRAWLER_RETRY_COUNT", "3")),
            update_interval=int(os.getenv("CRAWLER_UPDATE_INTERVAL", "86400"))
        )
    
    @classmethod
    def load_logging(cls) -> LoggingConfig:
        """로깅 설정 로드"""
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/nas_search.log")
        )
    
    @classmethod
    def load_nas_configs(cls) -> List[NASConfig]:
        """NAS 설정 동적 로드 (최대 10개)"""
        configs = []
        
        for i in range(1, 11):
            host_key = f"NAS_HOST_{i}"
            if host_key not in os.environ:
                break
                
            configs.append(NASConfig(
                host=os.getenv(host_key),
                share=os.getenv(f"NAS_SHARE_{i}", "share"),
                username=os.getenv(f"NAS_USERNAME_{i}", ""),
                password=os.getenv(f"NAS_PASSWORD_{i}", ""),
                name=os.getenv(f"NAS_NAME_{i}", f"NAS_{i}"),
                start_path=os.getenv(f"NAS_START_PATH_{i}", "")
            ))
        
        cls.NAS_CONFIGS = configs
        return configs
    
    @classmethod
    def validate(cls) -> bool:
        """설정 검증"""
        if not cls.NAS_CONFIGS:
            cls.load_nas_configs()
        
        if not cls.NAS_CONFIGS:
            print("Error: NAS configuration not found")
            return False
        
        es_config = cls.load_elasticsearch()
        if not all([es_config.host, es_config.username, es_config.password]):
            print("Error: Elasticsearch configuration incomplete")
            return False
        
        return True


# 글로벌 설정 인스턴스
ELASTICSEARCH = Config.load_elasticsearch()
CRAWLER = Config.load_crawler()
LOGGING = Config.load_logging()
