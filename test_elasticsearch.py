"""
Elasticsearch 연결 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("🔍 Elasticsearch 연결 테스트")
print("=" * 60)
print()

try:
    from elasticsearch import Elasticsearch
    print("✅ elasticsearch 라이브러리 임포트 성공")
except ImportError as e:
    print(f"❌ elasticsearch 라이브러리 임포트 실패: {e}")
    sys.exit(1)

from src.config import ELASTICSEARCH

print(f"📋 설정 정보:")
print(f"   - Host: {ELASTICSEARCH.host}")
print(f"   - Port: {ELASTICSEARCH.port}")
print(f"   - Index: {ELASTICSEARCH.index_name}")
print(f"   - SSL: {ELASTICSEARCH.use_ssl}")
print()

print("🔗 Elasticsearch 서버 연결 중...")

try:
    client = Elasticsearch([f"http://{ELASTICSEARCH.host}:{ELASTICSEARCH.port}"])
    
    # 연결 테스트
    info = client.info()
    print(f"✅ 연결 성공!")
    print()
    print(f"📊 서버 정보:")
    print(f"   - Version: {info['version']['number']}")
    print(f"   - Tagline: {info['tagline']}")
    print()
    
    # 인덱스 상태 확인
    indices = client.indices.get_alias(index="*")
    print(f"📂 존재하는 인덱스:")
    if indices:
        for idx in sorted(indices.keys()):
            print(f"   - {idx}")
    else:
        print("   (없음)")
    print()
    
except Exception as e:
    print(f"❌ 연결 실패: {e}")
    print()
    print("💡 해결 방법:")
    print("1. Docker Desktop이 실행 중인지 확인")
    print("2. Elasticsearch 컨테이너가 실행 중인지 확인: docker ps")
    print("3. 다시 시작: docker restart elasticsearch")
    print()
    sys.exit(1)

print("=" * 60)
print("✅ Elasticsearch 연결 테스트 완료!")
print("=" * 60)
