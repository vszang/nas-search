"""
NAS 크롤링 → Elasticsearch + RAG 인덱싱 파이프라인

사용법:
    python run_crawl_index.py [옵션]

옵션:
    --reset        인덱스 초기화 후 재인덱싱 (기본: 누적 인덱싱)
    --batch-size   배치 크기 (기본: 100)
    --no-content   파일 내용 추출 안 함 (메타데이터만 인덱싱)
    --no-rag       RAG 벡터 인덱싱 건너뜀 (메타데이터 인덱싱만)
    --smb          LOCAL_NAS_PATH 무시하고 SMB 직접 접속 강제
"""

import argparse
import logging
import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from src.crawler import MultiNASCrawler, FileType, FileMetadata
from src.indexer import FileIndexer
from src.content_extractor import extract_content, is_extractable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("pipeline")


def run_pipeline(reset: bool = False, batch_size: int = 100,
                 no_content: bool = False, no_rag: bool = False):
    """크롤링 → ES 인덱싱 → RAG 벡터 인덱싱 파이프라인 실행"""

    # 1. Elasticsearch 연결 및 인덱스 준비
    logger.info("=== Elasticsearch 인덱서 초기화 ===")
    try:
        indexer = FileIndexer()
    except Exception as e:
        logger.error(f"Elasticsearch 연결 실패: {e}")
        logger.error("Elasticsearch가 실행 중인지 확인하세요.")
        return

    if reset:
        logger.info("메타데이터 인덱스 초기화 중...")
        indexer.create_index()
    else:
        from src.config import ELASTICSEARCH
        try:
            indexer.client.indices.get(index=ELASTICSEARCH.index_name)
            logger.info(f"기존 인덱스 사용: {ELASTICSEARCH.index_name}")
        except Exception:
            logger.info(f"인덱스 생성: {ELASTICSEARCH.index_name}")
            indexer.create_index()

    # 2. RAG 시스템 초기화 (--no-rag 아닌 경우)
    rag = None
    if not no_rag:
        logger.info("=== RAG 시스템 초기화 ===")
        try:
            from src.rag_system_optimized import RAGSystemOptimized
            from src.config import ELASTICSEARCH
            rag = RAGSystemOptimized(
                es_host=ELASTICSEARCH.host,
                es_port=ELASTICSEARCH.port
            )
            if reset:
                logger.info("RAG 인덱스 초기화 중...")
                rag.create_index()
            else:
                try:
                    rag.es.indices.get(index=rag.index_name)
                    logger.info(f"기존 RAG 인덱스 사용: {rag.index_name}")
                except Exception:
                    logger.info(f"RAG 인덱스 생성: {rag.index_name}")
                    rag.create_index()
        except Exception as e:
            logger.warning(f"RAG 시스템 초기화 실패 (건너뜀): {e}")
            rag = None

    # 3. NAS 크롤러 초기화 및 연결
    logger.info("=== NAS 크롤러 연결 ===")
    crawler = MultiNASCrawler()
    connected = crawler.connect_all()
    if connected == 0:
        logger.error("연결된 NAS가 없습니다. .env 파일의 NAS 설정을 확인하세요.")
        return
    logger.info(f"{connected}개 NAS 연결 완료")

    # 4. 크롤링 + 인덱싱
    logger.info("=== 크롤링 및 인덱싱 시작 ===")
    total_crawled = 0
    total_es_indexed = 0
    total_rag_indexed = 0

    es_batch: list = []       # [(FileMetadata, content), ...]
    rag_batch: list = []      # [{file_path, content, ...}, ...]

    def flush_es():
        nonlocal total_es_indexed
        if not es_batch:
            return
        indexed = indexer.batch_index_files(es_batch)
        total_es_indexed += indexed
        logger.info(f"  ES 배치 인덱싱: {indexed}/{len(es_batch)} (누계 {total_es_indexed}개)")
        es_batch.clear()

    def flush_rag():
        nonlocal total_rag_indexed
        if not rag_batch or rag is None:
            return
        success, fail = rag.batch_index_documents(rag_batch)
        total_rag_indexed += success
        logger.info(f"  RAG 배치 인덱싱: {success}/{len(rag_batch)} (누계 {total_rag_indexed}개)")
        rag_batch.clear()

    for nas_crawler in crawler.crawlers:
        if not (nas_crawler.is_local_path or hasattr(nas_crawler, 'smb_base')):
            logger.warning(f"연결 안 된 크롤러 건너뜀: {nas_crawler.config.name}")
            continue

        logger.info(f"크롤링 시작: {nas_crawler.config.name}")
        nas_file_count = 0

        try:
            for metadata in nas_crawler.crawl():
                total_crawled += 1
                nas_file_count += 1

                content = ""
                if not no_content:
                    content = extract_content(metadata.path, file_size=metadata.size)

                # ES 배치에 추가
                es_batch.append((metadata, content))

                # RAG 배치에 추가 (내용 있는 텍스트 파일만)
                if rag is not None and content:
                    rag_batch.append({
                        "file_path": metadata.path,
                        "file_name": metadata.name,
                        "content": content,
                        "file_type": metadata.file_type.value,
                        "file_size": metadata.size,
                        "modified_date": metadata.modified.isoformat() if metadata.modified else "",
                        "nas_name": metadata.nas_name,
                    })

                if total_crawled % 50 == 0:
                    logger.info(f"  크롤링 중... {total_crawled}개 발견")

                if len(es_batch) >= batch_size:
                    flush_es()

                if len(rag_batch) >= batch_size:
                    flush_rag()

        except Exception as e:
            logger.error(f"크롤링 오류 ({nas_crawler.config.name}): {e}")

        logger.info(f"{nas_crawler.config.name} 완료: {nas_file_count}개 파일")

    # 남은 배치 처리
    flush_es()
    flush_rag()

    # 5. 결과 요약
    logger.info("=== 파이프라인 완료 ===")
    logger.info(f"크롤링: {total_crawled}개 파일")
    logger.info(f"ES 인덱싱: {total_es_indexed}개 파일")
    if rag is not None:
        logger.info(f"RAG 인덱싱: {total_rag_indexed}개 텍스트 파일 (벡터 검색 가능)")
    if total_crawled > 0:
        rate = total_es_indexed / total_crawled * 100
        logger.info(f"ES 성공률: {rate:.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NAS 크롤링 → Elasticsearch + RAG 인덱싱 파이프라인")
    parser.add_argument("--reset", action="store_true", help="인덱스 초기화 후 재인덱싱")
    parser.add_argument("--batch-size", type=int, default=100, help="배치 크기 (기본: 100)")
    parser.add_argument("--no-content", action="store_true", help="파일 내용 추출 안 함")
    parser.add_argument("--no-rag", action="store_true", help="RAG 벡터 인덱싱 건너뜀")
    args = parser.parse_args()

    run_pipeline(
        reset=args.reset,
        batch_size=args.batch_size,
        no_content=args.no_content,
        no_rag=args.no_rag,
    )
