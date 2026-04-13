#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
sys.path.insert(0, '.')

print('='*80)
print('Claude vs Gemini - MCP 도구 호출 테스트')
print('='*80)

from src.ai_factory import AIClientFactory

# Claude 테스트
print('\n1️⃣  Claude로 MCP 도구 호출')
print('-'*80)
print('질문: "ZIP 파일을 찾아줄 수 있을까?"')
print('처리 중...')
try:
    claude_client = AIClientFactory.create('claude')
    start = time.time()
    response = claude_client.chat('ZIP 파일을 찾아줄 수 있을까?')
    elapsed = time.time() - start
    print(f'✓ Claude 응답 성공 ({elapsed:.2f}초)')
    print(f'응답: {response[:200]}...')
except Exception as e:
    print(f'✗ Claude 에러: {str(e)[:200]}')

# Gemini 테스트
print('\n2️⃣  Gemini로 MCP 도구 호출')
print('-'*80)
print('질문: "ZIP 파일을 찾아줄 수 있을까?"')
print('처리 중...')
try:
    gemini_client = AIClientFactory.create('gemini')
    start = time.time()
    response = gemini_client.chat('ZIP 파일을 찾아줄 수 있을까?')
    elapsed = time.time() - start
    print(f'✓ Gemini 응답 성공 ({elapsed:.2f}초)')
    print(f'응답: {response[:200]}...')
except Exception as e:
    print(f'✗ Gemini 에러: {str(e)[:200]}')

print('\n' + '='*80)
print('도구 호출 테스트 완료')
print('='*80)
