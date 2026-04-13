#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from elasticsearch import Elasticsearch
from src.config import Config

print('Elasticsearch 연결 테스트...')
try:
    es_config = Config.load_elasticsearch()
    client = Elasticsearch([f"http://{es_config.host}:{es_config.port}"])
    info = client.info()
    print(f'✅ 연결 성공')
    print(f'버전: {info["version"]["number"]}')
    print(f'상태: {info["tagline"]}')
except Exception as e:
    print(f'❌ 연결 실패: {str(e)[:300]}')
