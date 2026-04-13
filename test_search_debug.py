"""
Elasticsearch 검색 디버그 테스트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.searcher import FileSearcher
from src.config import ELASTICSEARCH


def main():
    print()
    print("=" * 70)
    print("🔍 Elasticsearch 검색 디버그 테스트")
    print("=" * 70)
    print()
    
    searcher = FileSearcher()
    
    # 모든 문서 조회
    print("📋 모든 문서 조회")
    print("-" * 70)
    
    response = searcher.client.search(
        index=ELASTICSEARCH.index_name,
        query={"match_all": {}},
        size=100
    )
    
    docs = response['hits']['hits']
    print(f"✅ {len(docs)}개 문서 발견\n")
    
    # 문서 세부 정보 출력
    print("📄 문서 세부정보:")
    for i, doc in enumerate(docs[:3], 1):
        source = doc['_source']
        print(f"\n{i}. {source['name']}")
        print(f"   - Path: {source['path']}")
        print(f"   - Size: {source['size']} bytes ({source['size']/(1024*1024):.1f} MB)")
        print(f"   - Type: {source['file_type']}")
        print(f"   - NAS: {source['nas_name']}")
    print()
    
    # 파일 타입별 분류
    print("📊 파일 타입 분포")
    print("-" * 70)
    
    from collections import Counter
    types = Counter([doc['_source']['file_type'] for doc in docs])
    
    for file_type, count in sorted(types.items()):
        print(f"  - {file_type}: {count}개")
    print()
    
    # 크기별 분류
    print("📊 파일 크기 분포")
    print("-" * 70)
    
    for doc in docs:
        source = doc['_source']
        size_mb = source['size'] / (1024*1024)
        print(f"  - {source['name']}: {size_mb:.1f} MB")
    print()
    
    # 필터 쿼리 테스트
    print("🔎 필터 쿼리 테스트")
    print("-" * 70)
    
    # 테스트 1: archive 타입만
    print("\n테스트 1: archive 타입만")
    response = searcher.client.search(
        index=ELASTICSEARCH.index_name,
        query={
            "bool": {
                "filter": {"term": {"file_type": "archive"}}
            }
        }
    )
    print(f"✅ {len(response['hits']['hits'])}개 결과")
    
    # 테스트 2: 크기 범위 (100MB ~ 500MB)
    print("\n테스트 2: 크기 범위 (100MB ~ 500MB)")
    response = searcher.client.search(
        index=ELASTICSEARCH.index_name,
        query={
            "bool": {
                "filter": {
                    "range": {
                        "size": {
                            "gte": 100*1024*1024,
                            "lte": 500*1024*1024
                        }
                    }
                }
            }
        }
    )
    print(f"✅ {len(response['hits']['hits'])}개 결과")
    for doc in response['hits']['hits']:
        size_mb = doc['_source']['size'] / (1024*1024)
        print(f"  - {doc['_source']['name']}: {size_mb:.1f} MB")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()
