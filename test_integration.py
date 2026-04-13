"""
Elasticsearch 인덱싱 및 검색 통합 테스트
크롤러 → 인덱서 → 검색 파이프라인 테스트
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.config import Config
from src.crawler import MultiNASCrawler
from src.indexer import FileIndexer
from src.searcher import FileSearcher


def main():
    print()
    print("=" * 70)
    print("🔍 Elasticsearch 인덱싱 & 검색 통합 테스트")
    print("=" * 70)
    print()
    
    # ==================== 1단계: 크롤링 ====================
    print("📂 1단계: 파일 크롤링")
    print("-" * 70)
    
    multi_crawler = MultiNASCrawler()
    multi_crawler.connect_all()
    
    files = multi_crawler.crawl_all(recursive=False)
    print(f"✅ {len(files)}개 파일 크롤링 완료")
    print()
    
    # ==================== 2단계: 인덱싱 ====================
    print("📊 2단계: Elasticsearch 인덱싱")
    print("-" * 70)
    
    indexer = FileIndexer()
    
    # 인덱스 생성
    print("🏗️  인덱스 생성 중...")
    if indexer.create_index():
        print("✅ 인덱스 생성 성공")
    else:
        print("❌ 인덱스 생성 실패")
        return
    print()
    
    # 배치 인덱싱
    print("📝 파일 인덱싱 중...")
    files_with_content = [(f, "") for f in files]  # 빈 콘텐츠로 테스트
    
    indexed_count = indexer.batch_index_files(files_with_content)
    print(f"✅ {indexed_count}/{len(files)}개 파일 인덱싱 완료")
    print()
    
    # ==================== 3단계: 검색 ====================
    print("🔎 3단계: 파일 검색")
    print("-" * 70)
    
    searcher = FileSearcher()
    
    # 검색 테스트 1: 파일명 검색
    print("검색 1️⃣ : 파일명으로 검색 (*.zip)")
    results = searcher.search_by_name("zip", max_results=5)
    print(f"✅ {len(results)}개 결과 발견")
    for i, result in enumerate(results[:3], 1):
        print(f"   {i}. {result['name']} ({result['size']} bytes)")
    print()
    
    # 검색 테스트 2: 고급 검색 (파일 타입 필터)
    print("검색 2️⃣ : 고급 검색 (archive 타입만)")
    results = searcher.search_advanced(file_type="archive", max_results=5)
    print(f"✅ {len(results)}개 결과 발견")
    for i, result in enumerate(results[:3], 1):
        print(f"   {i}. {result['name']} ({result['file_type']})")
    print()
    
    # 검색 테스트 3: 크기 범위 검색
    print("검색 3️⃣ : 크기 범위 검색 (100MB ~ 500MB)")
    results = searcher.search_advanced(
        min_size=100*1024*1024,  # 100MB
        max_size=500*1024*1024,  # 500MB
        max_results=5
    )
    print(f"✅ {len(results)}개 결과 발견")
    for i, result in enumerate(results[:3], 1):
        size_mb = result['size'] / (1024*1024)
        print(f"   {i}. {result['name']} ({size_mb:.1f} MB)")
    print()
    
    # ==================== 4단계: 통계 ====================
    print("📊 4단계: 인덱스 통계")
    print("-" * 70)
    
    from src.config import ELASTICSEARCH
    client_info = searcher.client.info()
    
    index_stats = searcher.client.indices.stats(index=ELASTICSEARCH.index_name)
    doc_count = index_stats['indices'][ELASTICSEARCH.index_name]['primaries']['docs']['count']
    
    print(f"✅ Elasticsearch 버전: {client_info['version']['number']}")
    print(f"✅ 인덱스 이름: {ELASTICSEARCH.index_name}")
    print(f"✅ 총 문서 수: {doc_count}")
    print()
    
    print("=" * 70)
    print("✅ 모든 테스트 완료!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print(f"❌ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
