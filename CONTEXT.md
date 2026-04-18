# 프로젝트 컨텍스트

## 프로젝트 정의

**프로젝트명**: 사내 NAS 검색 시스템

**목표**: 사내 NAS 파일을 Elasticsearch + Claude AI로 자연어 검색

**아키텍처**: 풀스택 인덱싱 (Option 3)
- SMB 크롤러로 NAS 파일 탐색 및 내용 추출
- Elasticsearch에 메타데이터 + 내용 인덱싱
- Claude API tool_use 패턴으로 자연어 → 도구 호출
- Vue3 + Flask 웹 인터페이스

## 기술 스택

| 항목 | 선택 | 버전 |
|------|------|------|
| 언어 | Python | 3.12 |
| NAS 접근 | smbprotocol / smbclient | 1.16.1 |
| 검색 엔진 | Elasticsearch (Docker) | 8.11.0 |
| RAG 임베딩 | sentence-transformers | 3.3.1 |
| 딥러닝 | torch (CPU) | 2.2.0+cpu |
| AI (기본) | Claude Haiku | claude-haiku-4-5-20251001 |
| AI (고성능) | Claude Sonnet | claude-sonnet-4-6 |
| 웹 백엔드 | Flask + flask-cors | 3.1.x |
| 프론트엔드 | Vue3 + Vuetify + Vite | - |
| MCP SDK | mcp | 1.27.0 |

## 환경 정보

- **개발 서버**: Windows 10 Pro (현재 VM)
- **배포 서버**: 별도 서버 (IIS, 외부 IP 보유)
- **Elasticsearch**: Docker 컨테이너 (port 9200)
- **NAS**: Synology (SMB 포트 445)

## 주요 설계 결정

### 검색 방식
- 파일명 + 내용 통합 검색 (should = OR)
- 파일명 매칭 가중치 2배 (boost: 2)
- `searcher.py` → `search_by_keyword()` 메서드

### preview_file 우선순위
1. Elasticsearch에 저장된 content (path keyword 정확 매칭)
2. 로컬 텍스트 파일 직접 읽기
3. SMB content_extractor 실시간 추출 (세션 재연결 후)

### AI 클라이언트 구조
```
AIClient (추상 클래스)
├── ClaudeNASSearchClient   ← 현재 사용
├── GeminiNASSearchClient   ← 구현됨
└── (추후) LlamaCppClient   ← Gemma4 로컬 모델
```

### 파일 내용 추출 (content_extractor.py)
- PDF: pdfplumber
- DOCX: python-docx
- XLSX: openpyxl
- PPTX: python-pptx
- HWP: olefile PrvText 스트림 (UTF-16-LE) → pyhwp CLI 폴백
- 텍스트: utf-8 → cp949 → euc-kr → latin-1 순차 시도
- SMB 파일: 임시 파일 다운로드 후 파싱 → 삭제

### 인덱싱 전략
- ES 인덱스: `nas_files` (메타데이터 + 내용)
- RAG 인덱스: `nas_documents_v2` (벡터 임베딩)
- 최대 내용 크기: 5MB (다운로드), 50,000자 (인덱싱)
- 누적 인덱싱: 기존 데이터 유지하며 새 파일 추가

## 배포 구성

### Flask VM (현재 서버)
- Flask: `start_server.bat` → port 5000
- Elasticsearch: Docker (port 9200)
- 인덱싱: `run_index.bat` / `run_index_reset.bat`

### 배포 서버 (IIS)
- Frontend: `dist/` 정적 파일 서빙
- URL Rewrite: `/api/*` → Flask VM 내부 IP:5000
- ARR 프록시 필요

## ES 인덱스 매핑

```
nas_files:
  path: keyword          ← 정확 매칭 (term query)
  name: text + keyword   ← 전문검색 + 집계
  content: text          ← 전문검색 (korean_analyzer)
  file_type: keyword
  size: long
  modified: date
  nas_name: keyword
  indexed_at: date
```

## 환경변수 (.env)

```
NAS_HOST_1=192.168.0.101
NAS_SHARE_1=nas
NAS_START_PATH_1=test
NAS_USERNAME_1=admin
NAS_PASSWORD_1=...
NAS_NAME_1=Main NAS

ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX_NAME=nas_files

ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# LOCAL_NAS_PATH_1=C:\Source  ← 주석처리 = SMB 모드
```

## 다음 계획

1. **MCP 표준 서버** (`mcp_server_stdio.py`) - Claude Desktop 연결
2. **로컬 LLM** (`llama_cpp_integration.py`) - Gemma4 via llama-cpp-python
3. **자동 인덱싱** - Windows 작업 스케줄러
