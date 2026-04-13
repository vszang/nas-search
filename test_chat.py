#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/api/chat 엔드포인트 테스트
"""

import requests
import json

queries = [
    'Python 파일을 찾아줄래?',
    '최근에 수정된 파일들은 뭐야?',
    '가장 큰 파일들을 찾아줘'
]

for query in queries:
    print(f'\n❓ 질문: {query}')
    print('='*60)
    try:
        response = requests.post('http://localhost:5000/api/chat', 
            json={'message': query},
            timeout=10)
        data = response.json()
        if data.get('success'):
            print(f'✅ 답변:\n{data.get("response")}')
            if data.get('files'):
                print(f'\n📁 발견된 파일 ({len(data["files"])}개):')
                for f in data['files'][:3]:
                    print(f'  - {f.get("name")} (유사도: {f.get("score", 0):.2f})')
        else:
            print(f'❌ 에러: {data.get("error")}')
    except Exception as e:
        print(f'❌ 오류: {e}')
        import traceback
        traceback.print_exc()

print("\n✅ 테스트 완료\n")
