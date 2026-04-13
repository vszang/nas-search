# MCP를 웹사이트에 통합하는 방법

## 1. 아키텍처 개요

당신이 생각하는 구조를 구현하는 방법:

```
┌─────────────────────────────────────────────────────────────┐
│                      웹사이트 (프론트엔드)                    │
│              (React, Vue, HTML+JS 등)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ (HTTP/WebSocket)
                       │ "NAS에서 파일 찾아줘"
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   웹 백엔드 (당신 서버)                      │
│              (Python, Node.js, Django 등)                  │
│                                                             │
│  [AI API 선택 로직]                                        │
│  ├─ Claude API (Anthropic)                               │
│  ├─ Gemini API (Google)                                  │
│  └─ GPT API (OpenAI)                                     │
│       ↓                                                    │
│  [MCP 서버 호출]                                          │
│       ↓                                                    │
│  AI: "MCP를 사용해서 파일 검색 도구 호출해줘"             │
│  MCP: 검색 결과 반환                                      │
│  백엔드: 결과를 웹사이트에 응답                           │
└──────────┬──────────────────────────────────────────────────┘
           │
           │ (별도 프로세스)
           ▼
┌─────────────────────────────────────────────────────────────┐
│          MCP 서버 (사내 NAS 검색)                          │
│    (다른 머신 또는 같은 머신에서 실행)                      │
│                                                             │
│  ├─ search_files()                                        │
│  ├─ list_directory()                                      │
│  ├─ get_file_info()                                       │
│  └─ preview_file()                                        │
│       ↓                                                    │
│    SMB ← NAS 접근                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 구현 방식 비교

### 방식 A: 직접 MCP 프로세스 호출 ⭐ 권장

```python
# 웹 백엔드 (Django/Flask)

from anthropic import Anthropic
import subprocess
import json

class WebIntegration:
    def __init__(self):
        self.client = Anthropic()
        # MCP 서버 프로세스 시작
        self.mcp_process = subprocess.Popen(
            ["python", "D:\\Source\\intranet-nas-search\\src\\mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    def search_nas_files(self, user_query: str):
        """
        사용자 질문 → Claude API → MCP 호출 → 결과 반환
        """
        # 1️⃣ Claude API에 요청 (MCP 도구 사용)
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",  # 또는 다른 모델
            max_tokens=1024,
            tools=[
                {
                    "name": "search_files",
                    "description": "NAS에서 파일 검색",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "nas_path": {"type": "string"},
                            "file_type": {"type": "string"}
                        }
                    }
                },
                # ... 기타 도구들
            ],
            messages=[
                {
                    "role": "user",
                    "content": user_query  # "2024 보고서 PDF 찾아줄래?"
                }
            ]
        )
        
        # 2️⃣ 응답 처리 (도구 호출 결과)
        return {
            "status": "success",
            "results": response.content,
            "used_tool": "search_files"
        }
```

### 방식 B: REST API로 MCP 제공

```python
# MCP 서버에 REST API 래퍼 추가

from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/search', methods=['POST'])
def search_endpoint():
    """
    REST API: POST /api/search
    {
        "query": "보고서",
        "nas_path": "*",
        "file_type": "pdf"
    }
    """
    data = request.json
    
    # MCP 도구 직접 호출
    from nas_search import search_files
    results = search_files(
        data['query'],
        data['nas_path'],
        data.get('file_type')
    )
    
    return jsonify({
        "status": "success",
        "results": results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**웹 백엔드에서 호출:**
```python
import requests

response = requests.post('http://localhost:5000/api/search', json={
    "query": "2024 보고서",
    "nas_path": "*",
    "file_type": "pdf"
})

results = response.json()
```

---

## 3. 무료 AI API 선택 비교

### 3-1. Claude API (Anthropic) ⭐ 추천

**장점:**
- ✅ MCP 공식 지원 (Anthropic이 만듦)
- ✅ 최적화된 통합
- ✅ 강력한 도구 사용 능력
- ✅ 컨텍스트 윈도우 큼

**무료 Usage:**
```
Claude 3.5 Sonnet (권장):
- 월 150만 토큰 (약 1000번 요청)
- Tier 1 사용자 (초기): $5 크레딧 제공
- 초과 시: 유료 ($3/$15 per 1M tokens)
```

**구현:**
```python
from anthropic import Anthropic

client = Anthropic()

# MCP로부터 도구 정의 가져오기
tools = [
    {
        "name": "search_files",
        "description": "NAS 파일 검색",
        "input_schema": {...}
    }
]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[...]
)
```

---

### 3-2. Google Gemini API

**장점:**
- ✅ 무료 계층 더 관대
- ✅ 빠른 응답
- ✅ 멀티모달 지원

**무료 Usage:**
```
Gemini 2.0 Flash:
- 월 100만 토큰 (약 1000-2000 요청)
- RPM 제한: 2분당 100 요청
```

**단점:**
- ❌ MCP 미지원 (커스텀 도구 구현 필요)
- ❌ 도구 호출 다소 제한적

**구현:**
```python
import anthropic

# Gemini를 Anthropic SDK로 사용 가능
client = anthropic.Anthropic(
    api_key="gemini_api_key",
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

# Claude와 비슷하게 사용 가능
```

---

### 3-3. OpenAI GPT API

**장점:**
- ✅ 매우 강력한 모델
- ✅ Function Calling 지원

**무료 Usage:**
```
GPT-4o mini (경량):
- 초기 $5 크레딧 (3개월)
- 초과 시: 매우 비쌈
```

**단점:**
- ❌ 무료 크레딧 제한적
- ❌ MCP 미지원 (Anthropic 전용)
- ❌ 비싼 가격

**구현:**
```python
from openai import OpenAI

client = OpenAI(api_key="your_key")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "NAS 파일 검색",
                "parameters": {...}
            }
        }
    ]
)
```

---

## 4. 권장 구성

### 🎯 최적 조합: Claude + 선택사항 (Gemini/GPT)

```
1순위: Claude API
├─ 이유: MCP 공식 지원, 최고 호환성
├─ 무료 크레딧: $5 (충분)
└─ 폴백: 없음 (항상 Claude 사용)

2순위: Gemini API (비용 절감용)
├─ 이유: 무료 크레딧 더 많음
├─ 무료 크레딧: 월 100만 토큰
└─ 구현: 도구 수동 매핑 필요

3순위: GPT API (강력함이 필요할 때만)
├─ 이유: 최고 성능
├─ 무료 크레딧: $5 (제한적)
└─ 비용: 초과 시 비쌈
```

---

## 5. 실제 구현 예시

### 시나리오: 웹사이트에 "파일 검색" 기능

#### 1️⃣ 프론트엔드 (웹사이트)

```html
<!-- HTML -->
<form id="searchForm">
    <input type="text" id="query" placeholder="파일 검색...">
    <select id="fileType">
        <option value="">모든 타입</option>
        <option value=".pdf">PDF</option>
        <option value=".doc">Word</option>
        <option value=".xlsx">Excel</option>
    </select>
    <button type="submit">검색</button>
</form>

<div id="results"></div>

<script>
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const query = document.getElementById('query').value;
    const fileType = document.getElementById('fileType').value;
    
    // 백엔드에 요청
    const response = await fetch('/api/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query, fileType})
    });
    
    const data = await response.json();
    
    // 결과 표시
    document.getElementById('results').innerHTML = 
        data.results.map(r => `
            <div class="result">
                <strong>${r.name}</strong>
                <p>${r.path}</p>
                <small>${r.modified}</small>
            </div>
        `).join('');
});
</script>
```

#### 2️⃣ 백엔드 (당신 서버)

```python
# Flask 백엔드

from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic()

# MCP 도구 정의 (MCP 서버에서 가져옴)
MCP_TOOLS = [
    {
        "name": "search_files",
        "description": "NAS에서 파일 검색",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색어"},
                "file_type": {"type": "string", "description": "파일 타입"},
                "max_results": {"type": "integer", "description": "최대 결과 수"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_directory",
        "description": "NAS 폴더 목록 조회",
        "input_schema": {...}
    }
]

@app.route('/api/search', methods=['POST'])
def search_api():
    """
    사용자 쿼리 → Claude → MCP 도구 호출 → 결과 반환
    """
    data = request.json
    query = data['query']
    file_type = data.get('fileType', '')
    
    # 사용자 요청을 자연어로 변환
    user_message = f"사용자가 파일을 검색하려고 합니다: {query}"
    if file_type:
        user_message += f" (타입: {file_type})"
    
    try:
        # 1️⃣ Claude API 호출 (MCP 도구 사용)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=MCP_TOOLS,
            messages=[{
                "role": "user",
                "content": user_message
            }]
        )
        
        # 2️⃣ Claude 응답 처리
        # (도구 호출 결과를 반환)
        results = []
        for content in response.content:
            if hasattr(content, 'type') and content.type == 'tool_use':
                # MCP 도구 호출
                tool_result = call_mcp_tool(content.name, content.input)
                results.extend(tool_result)
        
        return jsonify({
            "status": "success",
            "results": results,
            "count": len(results)
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def call_mcp_tool(tool_name: str, inputs: dict):
    """MCP 서버의 도구 호출"""
    from nas_search import search_files, list_directory
    
    if tool_name == "search_files":
        return search_files(
            inputs['query'],
            inputs.get('file_type'),
            inputs.get('max_results', 50)
        )
    elif tool_name == "list_directory":
        return list_directory(inputs['path'])
    
    return []

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

#### 3️⃣ MCP 서버 (별도 프로세스)

```python
# src/mcp_server.py (또는 이미 구현한 것)

from nas_search import NASSearcher

searcher = NASSearcher()

def search_files(query: str, file_type: str = None, max_results: int = 50):
    """파일 검색 도구"""
    results = searcher.search(
        query=query,
        file_type=file_type,
        max_results=max_results
    )
    return results

def list_directory(path: str):
    """디렉토리 목록 도구"""
    return searcher.list_dir(path)

# 백엔드에서 import하여 사용
```

---

## 6. 배포 구조

### Windows Server 2019에서 실행

```
Windows Server 2019 (Hyper-V VM)
│
├─ 웹 백엔드 (포트 5000)
│  ├─ Flask/Django 서버
│  ├─ Claude API 호출 (인터넷)
│  └─ MCP 서버 호출 (로컬)
│
├─ MCP 서버 (포트 9000, 내부)
│  ├─ NAS 검색 기능
│  ├─ 파일 메타데이터
│  └─ 인덱싱 엔진
│
└─ 웹사이트 (포트 80/443)
   ├─ React/Vue 프론트엔드
   ├─ HTTPS (SSL 지원)
   └─ 백엔드와 통신 (API)
```

**실행 순차:**
```bash
# 1️⃣ MCP 서버 시작
python D:\Source\intranet-nas-search\src\mcp_server.py --port 9000

# 2️⃣ 웹 백엔드 시작
python web_backend/app.py --port 5000

# 3️⃣ 웹사이트 접속
https://your-domain.com
```

---

## 7. 각 AI API별 설정

### 7-1. Claude API 설정

```python
from anthropic import Anthropic
import os

# API Key 설정 (.env 파일)
os.environ['ANTHROPIC_API_KEY'] = 'your_api_key'

client = Anthropic()

# 또는 직접 전달
client = Anthropic(api_key='your_api_key')

# 모델 선택
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",  # 무료 크레딧 적합
    max_tokens=1024,
    tools=[...],
    messages=[...]
)
```

### 7-2. Gemini API 설정

```python
import anthropic

# Gemini를 Anthropic SDK로 사용
client = anthropic.Anthropic(
    api_key="gemini_api_key",
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

response = client.messages.create(
    model="gemini-2.0-flash",
    max_tokens=1024,
    tools=[...],  # 수동으로 매핑 필요
    messages=[...]
)
```

### 7-3. GPT API 설정

```python
from openai import OpenAI

client = OpenAI(api_key='your_api_key')

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "NAS 파일 검색",
                "parameters": {...}
            }
        }
    ]
)

# 도구 호출 결과 처리
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "search_files":
            # MCP 도구 호출
```

---

## 8. 비용 추정

| 서비스 | 무료 크레딧 | 월 사용량 추정 | 초과 시 가격 |
|--------|-----------|-------------|------------|
| **Claude** | $5-50 | 100-500 요청 | $3 per 1M tokens |
| **Gemini** | 월 100만 토큰 | 1000-2000 요청 | $0.075 per 1M tokens |
| **GPT** | $5 | 50-100 요청 | $0.15-$3 per 1M tokens |

**권장:** Claude 무료 크레딧으로 시작, 필요시 Gemini 병렬 사용

---

## 9. 구현 단계

### 1단계: Claude API 테스트 (1일)
```bash
pip install anthropic
python test_claude_integration.py
```

### 2단계: 웹 백엔드 통합 (2-3일)
```bash
pip install flask
python app.py
# http://localhost:5000/api/search 테스트
```

### 3단계: 프론트엔드 연결 (2-3일)
```bash
npm install react axios
# React 컴포넌트 구현
```

### 4단계: 배포 (2-3일)
```bash
# Windows Server 2019에 배포
# HTTPS/SSL 설정
# Docker 컨테이너화 (선택)
```

---

## 10. 최종 권장 안

### ✅ 당신의 상황에서 최적:

1. **Claude API 사용** (MCP 공식 지원, 최고 호환)
2. **무료 크레딧 활용** ($5-50, 충분)
3. **웹 백엔드 추가** (Flask, 간단)
4. **Gemini 백업** (크레딧 많음, 필요시)

### 예상 구현 일정:
- Week 1: MCP 서버 완성 ✅ (이미 계획 중)
- Week 2-3: 웹 백엔드 + Claude 통합
- Week 4: 프론트엔드 + 배포

### 예상 월 비용:
- **초기 1-2개월**: $0 (무료 크레딧)
- **이후**: $5-15/월 (Claude + Gemini 조합)

---

## 💡 핵심 요점

> **Q: 웹사이트 + AI API + MCP 연결이 가능한가?**
>
> **A: 완벽히 가능합니다!** ✅
>
> 1. 웹사이트 (프론트엔드)
> 2. ↓ (API 요청)
> 3. 웹 백엔드 (Claude API 호출)
> 4. ↓ (도구 호출)
> 5. MCP 서버 (NAS 검색)
>
> **이 구조로 무료 AI API를 사용할 수 있습니다!**

다음 단계는 다음 세션에서 진행하면 됩니다! 🚀
