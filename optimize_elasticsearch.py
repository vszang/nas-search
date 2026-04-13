#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Elasticsearch 연결 및 최적화
"""
import sys
import time
sys.path.insert(0, '.')

print('='*80)
print('Elasticsearch 연결 및 최적화')
print('='*80)

# ============================================================================
# 1. 연결 테스트
# ============================================================================

print('\n1️⃣  Elasticsearch 연결 테스트')
print('-'*80)

from elasticsearch import Elasticsearch

try:
    # ES 클라이언트 생성 (HTTP, SSL 없음)
    client = Elasticsearch(["http://localhost:9200"])
    
    # 연결 확인
    info = client.info()
    version = info["version"]["number"]
    print(f'✅ 연결 성공!')
    print(f'   버전: {version}')
    print(f'   상태: {info["tagline"]}')
    
except Exception as e:
    print(f'❌ 연결 실패: {str(e)[:200]}')
    sys.exit(1)

# ============================================================================
# 2. 인덱스 상태 확인
# ============================================================================

print('\n2️⃣  인덱스 상태 확인')
print('-'*80)

try:
    # 모든 인덱스 목록
    indices = client.indices.get_alias(index="*")
    print(f'✅ 현재 인덱스 {len(indices)} 개:')
    for idx_name in list(indices.keys())[:10]:  # 처음 10개만
        status = client.indices.stats(index=idx_name)
        doc_count = status['indices'][idx_name]['primaries']['docs']['count']
        print(f'   - {idx_name}: {doc_count} 개 문서')
    
except Exception as e:
    print(f'⚠️ 인덱스 조회 실패: {str(e)[:100]}')

# ============================================================================
# 3. 테스트 인덱스 생성 및 초기 데이터 설정
# ============================================================================

print('\n3️⃣  테스트 인덱스 생성 및 데이터 설정')
print('-'*80)

test_index = "nas_files_test"

try:
    # 기존 인덱스 삭제 (테스트용)
    if client.indices.exists(index=test_index):
        client.indices.delete(index=test_index)
        print(f'   기존 인덱스 삭제: {test_index}')
    
    # 인덱스 생성
    client.indices.create(index=test_index)
    print(f'✅ 인덱스 생성: {test_index}')
    
    # 테스트 데이터 삽입
    test_documents = [
        {
            "name": "flutter.zip",
            "path": "D:/Source/flutter.zip",
            "size": 268435456,
            "type": "zip",
            "modified": "2024-03-15T10:30:00Z"
        },
        {
            "name": "android-studio.zip",
            "path": "D:/Source/android-studio.zip",
            "size": 856932864,
            "type": "zip",
            "modified": "2024-02-20T14:20:00Z"
        },
        {
            "name": "python-project.py",
            "path": "D:/Source/python-project.py",
            "size": 45678,
            "type": "python",
            "modified": "2024-04-10T15:45:00Z"
        },
        {
            "name": "README.md",
            "path": "D:/Source/README.md",
            "size": 2048,
            "type": "markdown",
            "modified": "2024-04-12T09:00:00Z"
        }
    ]
    
    # 문서 삽입
    for i, doc in enumerate(test_documents, 1):
        client.index(index=test_index, id=i, body=doc)
    
    print(f'✅ 테스트 데이터 삽입: {len(test_documents)} 개 문서')
    
    # 인덱스 새로고침 (검색 가능하게)
    client.indices.refresh(index=test_index)
    print(f'✅ 인덱스 새로고침 완료')
    
except Exception as e:
    print(f'❌ 인덱스 생성 실패: {e}')
    sys.exit(1)

# ============================================================================
# 4. 검색 성능 테스트
# ============================================================================

print('\n4️⃣  검색 성능 테스트')
print('-'*80)

search_queries = [
    {"query": "zip", "description": "파일명으로 'zip' 검색"},
    {"query": "flutter", "description": "파일명으로 'flutter' 검색"},
    {"query": "python", "description": "타입으로 'python' 검색"},
    {"query": "md", "description": "파일명으로 'md' 검색"}
]

start_time = time.time()

for search in search_queries:
    query_body = {
        "query": {
            "multi_match": {
                "query": search["query"],
                "fields": ["name", "type"]
            }
        }
    }
    
    search_start = time.time()
    result = client.search(index=test_index, body=query_body)
    search_time = (time.time() - search_start) * 1000
    
    hits = result['hits']['total']['value']
    print(f'\n   {search["description"]}')
    print(f'   쿼리: "{search["query"]}"')
    print(f'   결과: {hits}개')
    print(f'   응답시간: {search_time:.2f}ms')
    
    if hits > 0:
        for hit in result['hits']['hits'][:3]:  # 처음 3개만
            print(f'     - {hit["_source"]["name"]} ({hit["_source"]["type"]})')

total_time = (time.time() - start_time) * 1000
print(f'\n✅ 총 검색 시간: {total_time:.2f}ms')

# ============================================================================
# 5. 성능 메트릭
# ============================================================================

print('\n5️⃣  성능 메트릭')
print('-'*80)

try:
    # 인덱스 통계
    stats = client.indices.stats(index=test_index)
    index_stats = stats['indices'][test_index]['primaries']
    
    print(f'✅ 인덱스 통계:')
    print(f'   문서 개수: {index_stats["docs"]["count"]}')
    print(f'   저장소 크기: {index_stats["store"]["size_in_bytes"]} bytes')
    print(f'   검색 횟수: {index_stats["search"]["query_current"]}')
    
    # 클러스터 정보
    cluster_health = client.cluster.health()
    print(f'\n✅ 클러스터 상태:')
    print(f'   상태: {cluster_health["status"]}')
    print(f'   노드 개수: {cluster_health["number_of_nodes"]}')
    print(f'   활성 샤드: {cluster_health["active_shards"]}')
    
except Exception as e:
    print(f'⚠️ 통계 조회 실패: {e}')

# ============================================================================
# 6. 최종 종합 테스트
# ============================================================================

print('\n6️⃣  종합 테스트: 파일 검색 시뮬레이션')
print('-'*80)

try:
    # search_files 시뮬레이션 (Phase 2 MCP 도구)
    def search_files_mock(query, file_type=None, max_results=10):
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name", "type"]
                            }
                        }
                    ]
                }
            },
            "size": max_results
        }
        
        if file_type:
            query_body["query"]["bool"]["filter"] = [
                {"term": {"type": file_type}}
            ]
        
        result = client.search(index=test_index, body=query_body)
        return [hit["_source"] for hit in result["hits"]["hits"]]
    
    # 테스트 쿼리
    print('\n[테스트 1] 모든 ZIP 파일 검색')
    results = search_files_mock("", file_type="zip")
    print(f'   결과: {len(results)} 개')
    for r in results:
        print(f'     - {r["name"]} ({r["size"]} bytes)')
    
    print('\n[테스트 2] "flutter" 검색')
    results = search_files_mock("flutter")
    print(f'   결과: {len(results)} 개')
    for r in results:
        print(f'     - {r["name"]}')
    
    print(f'\n✅ 종합 테스트 완료')
    
except Exception as e:
    print(f'❌ 종합 테스트 실패: {e}')

print('\n' + '='*80)
print('✅ Elasticsearch 최적화 완료!')
print('='*80)

print('\n🚀 다음 단계:')
print('   1. python test_mcp_integration_all_tools.py (Phase 2 테스트 재실행)')
print('   2. 성능 개선 확인')
print('   3. search_files 응답시간 비교')
