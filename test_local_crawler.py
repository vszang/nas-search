"""
로컬 테스트 스크립트
D:\Source의 파일들을 크롤링하는 테스트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

# 설정 및 크롤러 임포트
from src.config import Config
from src.crawler import NASCrawler, MultiNASCrawler


def test_config():
    """설정 로드 테스트"""
    print("=" * 60)
    print("🔍 테스트 1: 설정 로드")
    print("=" * 60)
    
    Config.load_nas_configs()
    
    print(f"✅ NAS 설정 수: {len(Config.NAS_CONFIGS)}")
    for i, config in enumerate(Config.NAS_CONFIGS, 1):
        print(f"  NAS {i}: {config.name}")
        print(f"    - Host: {config.host}")
        print(f"    - Share: {config.share}")
    print()


def test_single_crawler():
    """단일 크롤러 테스트"""
    print("=" * 60)
    print("🔍 테스트 2: 단일 NAS 크롤링")
    print("=" * 60)
    
    Config.load_nas_configs()
    
    if not Config.NAS_CONFIGS:
        print("❌ NAS 설정이 없습니다")
        return
    
    config = Config.NAS_CONFIGS[0]
    crawler = NASCrawler(config)
    
    # 연결
    print(f"🔗 {config.name}에 연결 중...")
    if not crawler.connect():
        print(f"❌ {config.name} 연결 실패")
        return
    
    print(f"✅ {config.name} 연결 성공")
    print(f"   로컬 경로 모드: {crawler.is_local_path}")
    print()
    
    # 로컬 경로 크롤링 (D:\Source\test_files)
    local_path = os.getenv("LOCAL_NAS_PATH_1")
    print(f"📂 크롤링 경로: {local_path}")
    print()
    
    files = []
    print("📄 발견된 파일:")
    print("-" * 60)
    
    for metadata in crawler.crawl(recursive=False):
        files.append(metadata)
        print(f"  📝 {metadata.name}")
        print(f"     - 경로: {metadata.path}")
        print(f"     - 크기: {metadata.size} bytes")
        print(f"     - 타입: {metadata.file_type.value}")
        print(f"     - NAS: {metadata.nas_name}")
        print()
    
    print(f"✅ 총 {len(files)}개 파일 발견")
    print()


def test_multi_crawler():
    """다중 크롤러 테스트"""
    print("=" * 60)
    print("🔍 테스트 3: 다중 NAS 크롤링")
    print("=" * 60)
    
    multi_crawler = MultiNASCrawler()
    
    print(f"🔗 {len(multi_crawler.crawlers)}개 NAS 연결 중...")
    connected = multi_crawler.connect_all()
    print(f"✅ {connected}/{len(multi_crawler.crawlers)} NAS 연결 성공")
    print()
    
    print("📂 모든 NAS 크롤링...")
    all_files = multi_crawler.crawl_all(recursive=False)
    
    print(f"✅ 총 {len(all_files)}개 파일 발견")
    print()
    
    # 타입별 분류
    by_type = {}
    for file_metadata in all_files:
        file_type = file_metadata.file_type.value
        if file_type not in by_type:
            by_type[file_type] = 0
        by_type[file_type] += 1
    
    print("📊 파일 타입 분포:")
    for file_type, count in sorted(by_type.items()):
        print(f"  - {file_type}: {count}개")
    print()


if __name__ == "__main__":
    print()
    print("𝖘 𝖙 𝖆 𝖗 𝖙   𝖓 𝖆 𝖘   𝖈 𝖗 𝖆 𝖜 𝖑 𝖊 𝖆   𝖙 𝖊 𝖘 𝖙 𝖘")
    print()
    
    try:
        test_config()
        test_single_crawler()
        test_multi_crawler()
        
        print("=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print(f"❌ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
