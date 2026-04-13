# Phase 3: Claude API 통합 - API 설정 가이드

## 1. Anthropic API Key 획득

### 1.1 API Key 발급
1. [Anthropic Console](https://console.anthropic.com) 방문
2. 로그인 (또는 계정 생성)
3. **"API keys"** 메뉴 클릭
4. **"Create Key"** 버튼 클릭
5. Key 이름 입력 (예: "NAS Search")
6. **"Create"** 클릭
7. API Key 복사 ⚠️ (한 번만 표시됨)

### 1.2 API Key 구성 확인
```
sk-ant-v3xxxxx...  (최소 100자 이상)
```

---

## 2. API Key 설정 방법

### 2.1 환경변수 설정 (권장)

#### Windows (PowerShell)
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-v3xxxxx..."
python example_chat.py
```

#### Windows (Command Prompt)
```cmd
set ANTHROPIC_API_KEY=sk-ant-v3xxxxx...
python example_chat.py
```

#### macOS/Linux (Bash)
```bash
export ANTHROPIC_API_KEY="sk-ant-v3xxxxx..."
python example_chat.py
```

#### macOS/Linux (zsh)
```zsh
export ANTHROPIC_API_KEY="sk-ant-v3xxxxx..."
python example_chat.py
```

### 2.2 .env 파일 설정

프로젝트 루트(`c:\Task\MCP\projects\intranet-nas-search`)에 `.env` 파일 생성:

```
# .env

# Claude API Key (Anthropic Console에서 발급)
ANTHROPIC_API_KEY=sk-ant-v3xxxxx...

# 선택사항: ES/SMB/Logging 설정
# ELASTICSEARCH_HOST=localhost
# ELASTICSEARCH_PORT=9200
# ELASTICSEARCH_USERNAME=elastic
# ELASTICSEARCH_PASSWORD=xxxxx
```

---

## 3. 실행 방법

### 3.1 대화형 채팅 모드
```bash
python example_chat.py
```

**명령어:**
- `exit`, `quit`, `종료`: 프로그램 종료
- `history`: 대화 기록 보기
- `clear`: 대화 기록 초기화
- `help`: 도움말

**예제 질문:**
```
👤 당신: ZIP 파일을 찾아줄 수 있을까?
🤖 Claude: 네, ZIP 파일을 검색해드리겠습니다...

👤 당신: flutter.zip 파일의 크기는?
🤖 Claude: flutter.zip 파일은 256MB입니다...

👤 당신: 텍스트 파일 내용 보여줄 수 있어?
🤖 Claude: 물론이죠. 텍스트 파일의 내용을 보여드리겠습니다...
```

### 3.2 데모 모드 (자동 실행)
```bash
python example_chat.py --demo
```

자동으로 몇 가지 질문을 실행한 후 종료됩니다.

### 3.3 도움말
```bash
python example_chat.py --help
```

---

## 4. 테스트 실행

### 4.1 통합 테스트
```bash
python test_claude_integration.py
```

**테스트 항목:**
1. ✓ 클라이언트 초기화
2. ✓ 도구 정의 스키마
3. ✓ 간단한 검색
4. ✓ 필터 포함 검색
5. ✓ 파일 정보 조회
6. ✓ 다중 턴 대화
7. ✓ 대화 히스토리 관리
8. ✓ 에러 처리

### 4.2 테스트 결과 해석

**성공:**
```
✓ 클라이언트 초기화
✓ 도구 정의 스키마
✓ 간단한 검색

✅ 모든 테스트 통과!
```

**실패:**
```
✗ API Key 누락
✗ 간단한 검색: 401 Unauthorized

⚠️ 2개 테스트 실패
```

---

## 5. 문제 해결

### 5.1 "API Key not found" 오류

**원인:** ANTHROPIC_API_KEY 환경변수가 설정되지 않음

**해결:**
```bash
# 1. 환경변수 설정 확인
echo $ANTHROPIC_API_KEY  # macOS/Linux
echo %ANTHROPIC_API_KEY%  # Windows cmd
$env:ANTHROPIC_API_KEY   # Windows PowerShell

# 2. 없으면 설정
export ANTHROPIC_API_KEY="sk-ant-v3xxxxx..."

# 3. 다시 실행
python example_chat.py
```

### 5.2 "401 Unauthorized" 오류

**원인:** API Key가 올바르지 않음

**해결:**
1. Anthropic Console에서 API Key 재확인
2. 복사할 때 공백 확인
3. Key 삭제 후 새로 생성
4. 환경변수 재설정

### 5.3 "Connection error" 오류

**원인:** 네트워크 연결 문제

**해결:**
- 인터넷 연결 확인
- VPN 사용 여부 확인
- Firewall 설정 확인
- 프록시 설정 필요 시 환경변수 추가:
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=https://proxy.example.com:8080
```

### 5.4 "Model not found" 오류

**원인:** API Key의 계정이 모델에 접근할 수 없음

**해결:**
- Anthropic Console에서 모델 접근 권한 확인
- 다른 모델명으로 변경 (src/claude_integration.py의 `self.model` 변수)

### 5.5 "Rate limit exceeded" 오류

**원인:** API 요청 제한 초과

**해결:**
- 요청 속도 감소
- 일부 요청 배치 처리
- 계정 업그레이드 고려

---

## 6. 고급 설정

### 6.1 모델 변경
`src/claude_integration.py`에서:

```python
# 기본값 (claude-3-5-sonnet-20241022)
self.model = "claude-3-5-sonnet-20241022"

# 다른 모델 옵션:
# "claude-3-opus-20250219"      (큰 작업용, 비용 높음)
# "claude-3-sonnet-20250229"    (권장, 균형 잡힌 성능/비용)
# "claude-3-haiku-20250307"     (빠른 응답, 비용 낮음)
```

### 6.2 시스템 프롬프트 변경
`src/claude_integration.py`에서:

```python
self.system_prompt = """
당신은 회사 내부의 NAS 파일 검색을 도와주는 AI 어시스턴트입니다.
사용자의 자연언어 질문을 이해하고 적절한 검색 도구를 사용합니다.

[커스텀 지시사항...]
"""
```

### 6.3 대화 컨텍스트 조정
메시지 히스토리 제한 추가:

```python
# src/claude_integration.py의 chat() 메서드에서
MAX_HISTORY = 20  # 최근 20개 메시지만 유지
if len(self.message_history) > MAX_HISTORY:
    self.message_history = self.message_history[-MAX_HISTORY:]
```

---

## 7. API 비용 관리

### 7.1 요금표 (2024년 기준)
- **claude-3-5-sonnet**: $3/M tokens (입력), $15/M tokens (출력)
- **claude-3-opus**: $15/M tokens (입력), $75/M tokens (출력)
- **claude-3-haiku**: $0.80/M tokens (입력), $4/M tokens (출력)

### 7.2 사용량 추적
```python
# src/claude_integration.py에서 usage 정보 로깅
response = self.client.messages.create(...)
print(f"사용 토큰: 입력 {response.usage.input_tokens}, 출력 {response.usage.output_tokens}")
```

### 7.3 비용 절감 팁
1. 짧은 쿼리 사용 (토큰 감소)
2. haiku 모델 사용 (비용 낮음)
3. 대화 히스토리 제한 (컨텍스트 감소)
4. 배치 처리 (API 호출 수 감소)

---

## 8. 보안 고려사항

### 8.1 API Key 보호
- ⚠️ **절대 공유하지 마세요**
- ⚠️ **Git에 커밋하지 마세요**
- ⚠️ **로그에 출력하지 마세요**

### 8.2 .env 파일 관리
```bash
# .gitignore에 추가
echo ".env" >> .gitignore
```

### 8.3 환경별 API Key 관리
```bash
# 개발: 개발용 Key
export ANTHROPIC_API_KEY="sk-ant-dev-xxxxx..."

# 프로덕션: 프로덕션용 Key
export ANTHROPIC_API_KEY="sk-ant-prod-xxxxx..."
```

---

## 9. 다음 단계

1. ✅ API Key 획득 및 설정
2. ✅ `python example_chat.py` 실행
3. ✅ 자연언어로 파일 검색
4. 📋 원하는 기능 추가 (예: 검색 결과 저장, 자동화 등)

---

## 10. 참고 자료

### 문서
- [Anthropic API Documentation](https://docs.anthropic.com)
- [API Reference](https://docs.anthropic.com/reference)
- [Models](https://docs.anthropic.com/models)

### 샘플 코드
- [Project Root]/example_chat.py - 대화형 인터페이스
- [Project Root]/test_claude_integration.py - 통합 테스트
- [Project Root]/src/claude_integration.py - 핵심 구현

### 지원
- 문제 발생 시: example_chat.py 실행 후 `help` 명령어 확인
- 테스트 실행: test_claude_integration.py로 각 기능 검증
