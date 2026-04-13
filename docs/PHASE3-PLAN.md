# Phase 3: Claude API 통합 상세 계획

## 📋 개요

Phase 2에서 완성한 4개 MCP 도구를 Claude API와 통합하여 자연언어로 파일을 검색하고 조회하는 시스템 구현

---

## 🎯 Phase 3 목표

1. ✅ Claude API 클라이언트 초기화
2. ✅ MCP 프로토콜 메시지 생성
3. ✅ 도구 정의 (Tools JSON Schema)
4. ✅ 사용자 요청 처리
5. ✅ 도구 호출 및 결과 반환
6. ✅ 대화 루프 구현
7. ✅ 테스트 및 검증

---

## 🔧 구현 구조

```
Claude API Client
├── 1. 초기화 (API key 설정)
├── 2. 메시지 생성 (사용자 요청)
├── 3. 도구 정의 (search_files, list_directory, get_file_info, preview_file)
├── 4. 도구 호출 (Claude의 요청에 따라)
├── 5. 결과 반환 (Claude에게 전달)
└── 6. 대화 루프 (반복)
```

---

## 📝 단계별 구현

### 1단계: Claude API 클라이언트 초기화

**파일:** `src/claude_integration.py`

```python
from anthropic import Anthropic

class ClaudeNASSearchClient:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.conversation_history = []
        
        # MCP 서버에서 도구 가져오기
        from .mcp_server import NASSearchMCPServer
        self.mcp_server = NASSearchMCPServer()
    
    def get_tools_schema(self) -> List[Dict]:
        """도구 정의 (JSON Schema)"""
        return [
            {
                "name": "search_files",
                "description": "NAS에서 파일 검색 (파일명, 내용, 고급 필터)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "검색어"},
                        "file_type": {"type": "string", "enum": [...]},
                        "max_results": {"type": "integer"}
                    },
                    "required": ["query"]
                }
            },
            # ... 다른 도구들
        ]
```

### 2단계: 메시지 생성 및 전송

```python
def chat(self, user_message: str) -> str:
    """사용자와 대화"""
    # 메시지 저장
    self.conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Claude API 호출
    response = self.client.messages.create(
        model=self.model,
        max_tokens=4096,
        tools=self.get_tools_schema(),
        messages=self.conversation_history
    )
    
    # 도구 호출 처리
    return self._handle_response(response)
```

### 3단계: 도구 호출 처리

```python
def _handle_response(self, response):
    """Claude 응답 처리 (도구 호출 여부 확인)"""
    
    # 도구 호출 없으면 완료
    if response.stop_reason == "end_turn":
        text_response = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": text_response
        })
        return text_response
    
    # 도구 호출 있으면 처리
    if response.stop_reason == "tool_use":
        # 도구 호출 결과 수집
        tool_results = []
        for content in response.content:
            if content.type == "tool_use":
                result = self._execute_tool(
                    content.name,
                    content.input
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": json.dumps(result)
                })
        
        # 대화 히스토리에 추가
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        self.conversation_history.append({
            "role": "user",
            "content": tool_results
        })
        
        # 다시 Claude 호출 (최종 답변 받기)
        final_response = self.client.messages.create(...)
        return self._handle_response(final_response)
```

### 4단계: 도구 실행

```python
def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
    """MCP 도구 실행"""
    logger.info(f"[Tool] {tool_name}: {tool_input}")
    
    # MCP 서버의 도구 호출
    result = getattr(self.mcp_server, tool_name)(**tool_input)
    
    logger.info(f"[Result] {tool_name}: {result}")
    return result
```

### 5단계: 대화 루프

```python
def interactive_chat(self):
    """대화형 모드"""
    print("NAS 검색 MCP - Claude AI 대화형 인터페이스")
    print("'exit' 또는 'quit'를 입력하면 종료합니다.\n")
    
    while True:
        user_input = input("당신: ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            print("대화를 종료합니다.")
            break
        
        if not user_input:
            continue
        
        response = self.chat(user_input)
        print(f"\nClaude: {response}\n")
```

---

## 📦 필요한 설정

### API Key 관리

**방식 1: 환경변수**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**.env 파일**
```
ANTHROPIC_API_KEY=sk-ant-...
```

### 도구 정의 (JSON Schema)

모든 4개 도구의 정의:

```json
{
  "name": "search_files",
  "description": "NAS에서 파일 검색",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "검색 키워드 (파일명 또는 내용)"
      },
      "file_type": {
        "type": "string",
        "enum": ["document", "text", "image", "video", "audio", "archive", "code"],
        "description": "파일 타입 필터"
      },
      "max_results": {
        "type": "integer",
        "default": 50,
        "description": "최대 결과 수"
      }
    },
    "required": ["query"]
  }
}
```

---

## 🧪 테스트 케이스

### 테스트 1: 간단한 검색
```
사용자: "ZIP 파일을 찾아줄 수 있을까?"
기대: Claude가 search_files 도구 호출 → 결과 반환
```

### 테스트 2: 필터를 포함한 검색
```
사용자: "100MB 이상 500MB 이하의 압축 파일이 있나요?"
기대: list_directory + search_files 조합 호출
```

### 테스트 3: 파일 정보 조회
```
사용자: "flutter.zip 파일의 크기는?"
기대: get_file_info 도구 호출 → 파일 정보 반환
```

### 테스트 4: 미리보기
```
사용자: "test.txt 파일 내용 보여줄 수 있어?"
기대: preview_file 도구 호출 → 파일 미리보기
```

### 테스트 5: 복잡한 대화
```
사용자: "가장 큰 ZIP 파일이 뭔가요?"
기대: 1) list_directory 호출 2) 분석 3) get_file_info로 정보 조회
```

---

## 📊 구현 체크리스트

### 코드 구현
- [ ] `src/claude_integration.py` - ClaudeNASSearchClient 클래스
- [ ] 도구 정의 JSON Schema (4개 모두)
- [ ] 메시지 관리 (대화 히스토리)
- [ ] 도구 호출 처리 로직
- [ ] 에러 처리 및 로깅

### 테스트
- [ ] 각 도구별 호출 테스트 (4개)
- [ ] 복합 쿼리 테스트 (3개)
- [ ] 에러 케이스 테스트 (3개)
- [ ] 성능 테스트

### 문서
- [ ] claude_integration.py 사용법
- [ ] API Key 설정 가이드
- [ ] 대화형 모드 사용법
- [ ] 트러블슈팅 가이드

---

## 🎯 Phase 3 완료 조건

- ✅ ClaudeNASSearchClient 클래스 구현
- ✅ 4개 도구 모두 JSON Schema 정의
- ✅ 도구 호출 및 결과 처리 로직
- ✅ 대화 히스토리 관리
- ✅ 대화형 인터페이스
- ✅ 포괄적인 테스트 (10+ 테스트 케이스)
- ✅ 예제 및 사용 설명서

---

## ⏱️ 예상 일정

| 작업 | 기간 |
|------|------|
| ClaudeNASSearchClient 구현 | 30분 |
| 도구 정의 (JSON Schema) | 20분 |
| 메시지 처리 로직 | 30분 |
| 도구 호출 처리 | 20분 |
| 테스트 작성 및 실행 | 40분 |
| 문서 작성 | 20분 |
| **총계** | **2시간** |

---

## 🚀 구현 순서

1. **src/claude_integration.py** 작성 (ClaudeNASSearchClient)
2. **도구 정의** JSON Schema 작성
3. **테스트 파일** 작성 (test_claude_integration.py)
4. **통합 테스트** 실행 (test_claude_full_workflow.py)
5. **샘플 코드** 작성 (example_chat.py)
6. **문서** 업데이트

---

## 핵심 개념

### MCP 프로토콜 메시지 흐름

```
1. 사용자 메시지
   → "ZIP 파일을 찾아줄 수 있을까?"

2. Claude 수신 및 분석
   → 도구 호출이 필요하다고 판단

3. 도구 호출 요청
   → {
       "type": "tool_use",
       "name": "search_files",
       "input": {"query": "ZIP"}
     }

4. 도구 실행
   → search_files("ZIP") = {
       "success": true,
       "data": {
         "files": [...],
         "total_count": 2,
         "elapsed_ms": 15
       }
     }

5. 결과 반환
   → Claude에게 결과 전달

6. 최종 응답
   → Claude가 결과를 바탕으로 자연언어 답변 생성
```

---

## 보안 고려사항

### API Key 보호
- ✅ 환경변수로 관리
- ✅ .env 파일 .gitignore 추가
- ✅ 로그에 API Key 출력 금지

### 도구 호출 검증
- ✅ 입력 파라미터 유효성 검사
- ✅ 경로 보안 검증
- ✅ 타임아웃 설정

### 에러 처리
- ✅ API 호출 실패 처리
- ✅ 도구 실행 오류 처리
- ✅ 네트워크 오류 전략

---

총 예상 기간: **2시간**

다음 단계: 구현 시작! 🎯
