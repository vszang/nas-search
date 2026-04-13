#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG 검색 최적화 성능 벤치마크
"""

import time
import json
from typing import List, Dict

def benchmark_embedding_cache():
    """임베딩 캐싱 성능 테스트"""
    print("\n" + "="*60)
    print("1️⃣  임베딩 캐싱 성능 테스트")
    print("="*60)
    
    from src.rag_system_optimized import get_rag_system
    
    rag = get_rag_system()
    if not rag:
        print("❌ RAG 시스템 초기화 실패")
        return
    
    test_text = "Python 프로그래밍 언어와 머신러닝 알고리즘에 대한 설명"
    
    # 첫 번째 임베딩 (캐시 미스)
    print(f"\n📝 테스트 텍스트: {test_text[:50]}...")
    
    start = time.time()
    vector1 = rag.encode_text(test_text)
    time1 = time.time() - start
    print(f"✅ 첫 번째 임베딩 (캐시 미스): {time1*1000:.2f}ms")
    
    # 두 번째 임베딩 (캐시 히트)
    start = time.time()
    vector2 = rag.encode_text(test_text)
    time2 = time.time() - start
    print(f"⚡ 두 번째 임베딩 (캐시 히트): {time2*1000:.2f}ms")
    
    # 캐시 효과
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"🚀 성능 향상: {speedup:.1f}배")
    
    stats = rag.get_cache_stats()
    print(f"📊 캐시 통계: {json.dumps(stats, ensure_ascii=False, indent=2)}")


def benchmark_batch_encoding():
    """배치 임베딩 성능 테스트"""
    print("\n" + "="*60)
    print("2️⃣  배치 임베딩 성능 테스트")
    print("="*60)
    
    from src.rag_system_optimized import get_rag_system
    
    rag = get_rag_system()
    if not rag:
        return
    
    texts = [
        f"문서 {i}: 이는 {i}번째 샘플 텍스트입니다. 장기 기억을 테스트하기 위한 내용입니다."
        for i in range(100)
    ]
    
    print(f"\n📚 테스트 대상: {len(texts)}개 문서")
    
    # 개별 인코딩
    start = time.time()
    vectors_individual = [rag.encode_text(text) for text in texts[:10]]  # 10개만 (시간 절약)
    time_individual = time.time() - start
    print(f"순차 처리 (10개): {time_individual*1000:.2f}ms")
    
    # 배치 인코딩
    start = time.time()
    vectors_batch = rag.batch_encode(texts, batch_size=32)
    time_batch = time.time() - start
    print(f"배치 처리 (100개): {time_batch*1000:.2f}ms")
    
    # 성능 비교
    speedup = (time_individual / 10) * 100 / time_batch  # 외삽
    print(f"🚀 배치 처리가 {speedup:.1f}배 빠름")


def benchmark_search():
    """검색 성능 테스트"""
    print("\n" + "="*60)
    print("3️⃣  검색 성능 테스트")
    print("="*60)
    
    from src.rag_system_optimized import get_rag_system
    
    rag = get_rag_system()
    if not rag:
        return
    
    queries = [
        "Python 프로그래밍",
        "데이터 분석",
        "머신러닝",
        "Python 프로그래밍",  # 반복 (캐시 미스 테스트)
    ]
    
    total_time_miss = 0
    total_time_hit = 0
    
    for i, query in enumerate(queries):
        start = time.time()
        results = rag.search_with_content(query, top_k=3)
        elapsed = time.time() - start
        
        cache_type = "미스 (첫 검색)" if i < 3 else "히트 (반복)"
        print(f"  검색 {i+1}: '{query}' → {len(results)}개 결과, {elapsed*1000:.2f}ms ({cache_type})")
        
        if i < 3:
            total_time_miss += elapsed
        else:
            total_time_hit += elapsed
    
    avg_miss = total_time_miss / 3
    avg_hit = total_time_hit / 1 if total_time_hit > 0 else 0.001
    
    if avg_hit > 0:
        speedup = avg_miss / avg_hit
        print(f"\n🚀 캐시 히트 성능: {speedup:.1f}배 빠름")
    
    stats = rag.get_cache_stats()
    print(f"📊 최종 캐시 통계:")
    print(f"   히트율: {stats['hit_rate']}")
    print(f"   캐시된 쿼리: {stats['cached_queries']}개")


def benchmark_cache_effectiveness():
    """캐시 효율성 테스트"""
    print("\n" + "="*60)
    print("4️⃣  캐시 효율성 테스트")
    print("="*60)
    
    from src.rag_system_optimized import get_rag_system
    
    rag = get_rag_system()
    if not rag:
        return
    
    # 반복 쿼리
    query = "머신러닝 알고리즘"
    
    print(f"\n🔄 쿼리 반복 테스트: '{query}'")
    print("   1차: 캐시 미스")
    
    start = time.time()
    rag.search(query, top_k=3)
    time_first = time.time() - start
    
    times = [time_first]
    
    for i in range(9):
        start = time.time()
        rag.search(query, top_k=3)
        elapsed = time.time() - start
        times.append(elapsed)
        if i == 0:
            print(f"   2차: 캐시 히트")
    
    avg_miss = times[0]
    avg_hit = sum(times[1:]) / len(times[1:])
    
    print(f"\n📊 결과:")
    print(f"   캐시 미스 (첫 검색): {avg_miss*1000:.2f}ms")
    print(f"   캐시 히트 (평균): {avg_hit*1000:.2f}ms")
    print(f"   성능 향상: {avg_miss/avg_hit:.1f}배")
    
    stats = rag.get_cache_stats()
    print(f"\n📈 최종 통계:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 캐시 초기화
    rag.clear_caches()
    print("\n🗑️  캐시 초기화 완료")


def main():
    """메인 벤치마크"""
    print("\n" + "🚀 "*30)
    print("RAG 검색 최적화 성능 벤치마크")
    print("🚀 "*30)
    
    try:
        # 1. 임베딩 캐시 테스트
        benchmark_embedding_cache()
        
        # 2. 배치 임베딩 테스트
        benchmark_batch_encoding()
        
        # 3. 검색 성능 테스트
        benchmark_search()
        
        # 4. 캐시 효율성 테스트
        benchmark_cache_effectiveness()
        
        print("\n" + "="*60)
        print("✅ 모든 벤치마크 완료!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 벤치마크 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
