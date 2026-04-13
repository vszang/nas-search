#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
sys.path.insert(0, '.')

print('='*80)
print('Gemini API 재테스트')
print('='*80)

from src.ai_factory import AIClientFactory

print('\n테스트: Gemini API 호출')
print('-'*80)
print('질문: "ZIP 파일을 찾아줄 수 있을까?"')
print('처리 중...')
print()

try:
    gemini_client = AIClientFactory.create('gemini')
    start = time.time()
    response = gemini_client.chat('ZIP 파일을 찾아줄 수 있을까?')
    elapsed = time.time() - start
    
    print(f'✅ Gemini 응답 성공 ({elapsed:.2f}초)')
    print('-'*80)
    print(f'응답:\n{response}')
    print('-'*80)
    print(f'응답 길이: {len(response)} 문자')
    
except Exception as e:
    print(f'❌ Gemini 에러')
    print('-'*80)
    print(f'에러 타입: {type(e).__name__}')
    print(f'에러 메시지:\n{str(e)[:500]}')
    print('-'*80)

print('\n' + '='*80)
print('테스트 완료')
print('='*80)
