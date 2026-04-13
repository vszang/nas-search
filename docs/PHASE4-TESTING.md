# Phase 4: Claude API 테스트 & 검증

## 목표
실제 Claude API를 사용하여 MCP 도구 통합을 검증하고 end-to-end 동작을 확인

## Phase 4 체크리스트

### 4-1: 사전 준비 ✅/⏳
- [ ] **4-1-1**: Elasticsearch 실행 확인
  ```bash
  # Docker에서 실행 중인지 확인
  docker ps | grep elasticsearch
  
  # 또는 직접 접속
  curl http://localhost:9200
  ```
  
- [ ] **4-1-2**: MCP 도구들 동작 확인
  ```bash
  # Phase 2 테스트 실행
  pytest test_mcp_search_files.py -v
  pytest test_mcp_list_directory.py -v
  pytest test_mcp_get_file_info.py -v
  pytest test_mcp_preview_file.py -v
  ```
  
- [ ] **4-1-3**: .env 파일 확인
  ```bash
  # 현재 설정 확인
  cat .env
  ```

### 4-2: API Key 설정

#### 옵션 A: 환경변수 설정 (PowerShell)
```powershell
# PowerShell에서 한 번만 설정하면 현재 세션에서 유효
$env:ANTHROPIC_API_KEY = "sk-ant-v3xxxxx..."

# 설정 확인
Write-Host $env:ANTHROPIC_API_KEY

# 이후 Python 스크립트 실행
python test_claude_integration.py
```

#### 옵션 B: .env 파일 설정 (권장)
```bash
# 프로젝트 루트에 .env 파일 있는지 확인
cat .env

# 없으면 생성
echo "ANTHROPIC_API_KEY=sk-ant-v3xxxxx..." > .env

# .env에 다음 내용 추가:
# ANTHROPIC_API_KEY=sk-ant-v3xxxxx...
```

**주의:** `.env` 파일을 `.gitignore`에 확인하여 API Key가 Git에 커밋되지 않도록 함
```bash
cat .gitignore | grep ".env"
```

### 4-3: 통합 테스트 실행

#### 테스트 1: 클라이언트 초기화 테스트
```bash
python -c "
from src.claude_integration import ClaudeNASSearchClient
client = ClaudeNASSearchClient()
print('✓ 클라이언트 초기화 성공')
print(f'  모델: {client.model}')
print(f'  도구 개수: {len(client.get_tools_schema())}')
"
```

**기대 결과:**
```
✓ 클라이언트 초기화 성공
  모델: claude-3-5-sonnet-20241022
  도구 개수: 4
```

#### 테스트 2: 기본 통합 테스트
```bash
python test_claude_integration.py
```

**기대 결과:**
- 8개 테스트 중 최소 6개 이상 통과
- 실패 원인: API 요청 속도 제한 또는 네트워크 연결

#### 테스트 3: 개별 도구 테스트

**테스트 3-1: 검색 (search_files)**
```bash
python -c "
from src.claude_integration import ClaudeNASSearchClient
client = ClaudeNASSearchClient()
response = client.chat('ZIP 파일 찾아줄 수 있을까?')
print(response)
"
```

**기대 결과:**
```
Claude가 search_files 도구를 호출하여:
- ZIP 파일 검색 수행
- 결과를 자연언어로 설명
예: "ZIP 파일을 찾았습니다. C#.zip (1.6GB)과 새 폴더2.zip (1.45GB)이 있습니다."
```

**테스트 3-2: 파일 정보 (get_file_info)**
```bash
python -c "
from src.claude_integration import ClaudeNASSearchClient
client = ClaudeNASSearchClient()
response = client.chat('flutter.zip 파일의 크기는?')
print(response)
"
```

**기대 결과:**
```
Claude가 get_file_info 도구를 호출하여:
- flutter.zip 파일 정보 조회
- 크기를 자연언어로 보고
예: "flutter.zip 파일은 256MB입니다."
```

**테스트 3-3: 디렉토리 목록 (list_directory)**
```bash
python -c "
from src.claude_integration import ClaudeNASSearchClient
client = ClaudeNASSearchClient()
response = client.chat('NAS에 어떤 파일들이 있어?')
print(response)
"
```

**기대 결과:**
```
Claude가 list_directory 도구를 호출하여:
- NAS의 파일 목록 조회
- 파일 개수 및 유형 보고
예: "NAS에는 총 12개의 파일이 있습니다. 압축 파일 11개, 텍스트 파일 1개 등..."
```

### 4-4: 대화형 모드 검증

#### 기본 실행
```bash
python example_chat.py
```

**상호 작용 시나리오:**
```
🚀 Claude AI 클라이언트 초기화 중...
✓ 클라이언트 초기화 완료
✓ 4개의 도구 로드됨: search_files, list_directory, get_file_info, preview_file

============================================================
🔍 NAS 파일 검색 - Claude AI 챗봇
============================================================

💬 자연언어로 파일을 검색해보세요!

👤 당신: ZIP 파일 찾아줄 수 있을까?
🤖 Claude: 네, ZIP 파일을 검색해드리겠습니다...
           (자동으로 search_files 도구 호출)

👤 당신: 가장 큰 파일은?
🤖 Claude: 가장 큰 파일은 C#.zip으로 1.6GB입니다.

👤 당신: 종료
```

**명령어 테스트:**
```
👤 당신: history
📋 대화 기록:
1. [USER] ZIP 파일 찾아줄 수 있을까?
2. [ASSISTANT] (응답)
...

👤 당신: clear
✓ 대화 기록이 초기화되었습니다.

👤 당신: help
📚 사용 가능한 명령어:
...
```

### 4-5: 성능 측정

#### 성능 테스트 스크립트
```bash
python -c "
import time
from src.claude_integration import ClaudeNASSearchClient

client = ClaudeNASSearchClient()

queries = [
    'ZIP 파일 찾아줄 수 있을까?',
    '텍스트 파일이 있어?',
    'flutter.zip 파일의 크기는?'
]

for i, query in enumerate(queries, 1):
    print(f'\n테스트 {i}: {query}')
    start = time.time()
    response = client.chat(query)
    elapsed = time.time() - start
    print(f'  응답 시간: {elapsed:.2f}초')
    print(f'  응답: {response[:100]}...')
"
```

**목표:**
- 각 쿼리 응답 시간: 2-5초 (API 레이턴시 포함)
- MCP 도구 실행 시간: 1초 이내
- 전체 파이프라인: 3-6초

### 4-6: 에러 처리 검증

#### 에러 시나리오 1: 잘못된 파일 경로
```bash
python -c "
from src.claude_integration import ClaudeNASSearchClient
client = ClaudeNASSearchClient()
response = client.chat('존재하지않는파일.txt 파일 정보 보여줄 수 있어?')
print(response)
"
```

**기대 결과:** Claude가 에러를 처리하고 친화적인 메시지 표시

#### 에러 시나리오 2: API Key 누락
```bash
# API Key 환경변수 제거
$env:ANTHROPIC_API_KEY = ""

python test_claude_integration.py
```

**기대 결과:** 명확한 에러 메시지 및 설정 가이드 표시

#### 에러 시나리오 3: Elasticsearch 연결 실패
```bash
# Elasticsearch 중지
docker stop elasticsearch

python -c "
from src.claude_integration import ClaudeNASSearchClient
client = ClaudeNASSearchClient()
response = client.chat('파일 찾아줄 수 있을까?')
"
```

**기대 결과:** MCP 도구의 에러 처리로 친화적인 응답 반환

### 4-7: 다중 턴 대화 검증

#### 대화 히스토리 테스트
```bash
python -c "
from src.claude_integration import ClaudeNASSearchClient
client = ClaudeNASSearchClient()

# 첫 번째 턴
print('턴 1: ZIP 파일 찾기')
r1 = client.chat('ZIP 파일 찾아줄 수 있을까?')
print(f'응답: {r1[:50]}...')
print(f'히스토리: {len(client.get_history())} 항목')

# 두 번째 턴
print('\n턴 2: 가장 큰 파일')
r2 = client.chat('그 중에 가장 큰 것은?')
print(f'응답: {r2[:50]}...')
print(f'히스토리: {len(client.get_history())} 항목')

# 세 번째 턴
print('\n턴 3: 크기 정보')
r3 = client.chat('그 파일은 몇 GB야?')
print(f'응답: {r3[:50]}...')
print(f'히스토리: {len(client.get_history())} 항목')
"
```

**기대 결과:**
- 각 턴마다 히스토리 항목 증가 (2배씩 증가: user + assistant)
- 마지막 턴에서 이전 대화 컨텍스트 유지

### 4-8: 실제 시나리오 테스트

#### 시나리오 1: 파일 검색 워크플로우
```
사용자: "최근에 수정된 텍스트 파일이 있나요?"
Claude: (list_directory) → (필터링) → "README.md가 텍스트 파일입니다"

사용자: "그 파일의 내용을 보여줄 수 있어?"
Claude: (preview_file) → (내용 반환) → "파일 내용은 다음과 같습니다..."
```

#### 시나리오 2: 파일 정보 워크플로우
```
사용자: "SDK 폴더에서 가장 큰 파일은?"
Claude: (list_directory) → (get_file_info 반복) → "flutter.zip이 가장 큽니다 (256MB)"

사용자: "그거 압축을 풀 때 얼마나 필요해?"
Claude: (get_file_info) → "약 512MB 정도 필요합니다"
```

#### 시나리오 3: 메타데이터 검색
```
사용자: "100MB 이상 500MB 이하의 파일을 찾아줄 수 있어?"
Claude: (search_files with size filter) → "새 폴더2.zip (1.45GB)은 범위를 벗어났습니다..."
```

---

## 문제 해결 (Troubleshooting)

### 문제 1: "API Key not found"
**해결:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-v3xxxxx..."
Write-Host $env:ANTHROPIC_API_KEY  # 설정 확인
```

### 문제 2: "401 Unauthorized"
**해결:**
- API Key 복사 시 공백 확인
- API Key 유효성 [Anthropic Console](https://console.anthropic.com) 확인

### 문제 3: "Connection error"
**해결:**
- 인터넷 연결 확인
- VPN/프록시 설정 확인
- Firewall 설정 확인

### 문제 4: "Elasticsearch connection error"
**해결:**
```bash
# Elasticsearch 상태 확인
docker ps | grep elasticsearch

# 재시작
docker restart elasticsearch

# 로그 확인
docker logs elasticsearch
```

### 문제 5: "Model not found"
**해결:**
- API 계정 업그레이드 확인
- src/claude_integration.py의 model 변수 확인

---

## Phase 4 완료 기준

✅ **완료 조건:**
1. ✅ 클라이언트 초기화 성공
2. ✅ 기본 통합 테스트 통과 (6개 이상)
3. ✅ 각 도구별 개별 테스트 성공 (search, info, list)
4. ✅ 대화형 모드 실행 및 명령어 작동
5. ✅ 성능 메트릭 달성 (3-6초)
6. ✅ 에러 처리 작동 확인
7. ✅ 다중 턴 대화 작동
8. ✅ 실제 시나리오 테스트 완료

---

## 다음 단계 (Phase 5)

Phase 4 완료 후:
- Flask/Django 웹 백엔드 구현
- REST API로 MCP 서버 노출
- 웹 프론트엔드 (선택사항)
- 배포 및 모니터링

---

## 참고 자료

- [PHASE3-API-SETUP.md](PHASE3-API-SETUP.md) - API 설정 상세 가이드
- [docs/README.md](README.md) - 전체 프로젝트 가이드
- [example_chat.py](../example_chat.py) - 사용 예제
- [test_claude_integration.py](../test_claude_integration.py) - 테스트 코드
