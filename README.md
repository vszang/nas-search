# 사내 NAS 검색 시스템

사내 NAS 파일을 Elasticsearch + Claude AI로 자연어 검색하는 웹 애플리케이션입니다.

## 아키텍처

```
브라우저 (Vue3 + Vuetify)
    ↓ HTTP /api/*
Flask API 서버 (app.py, port 5000)
    ↓
Claude AI (tool_use)
    ↓
NASSearchMCPServer
    ├─ Elasticsearch (port 9200) ← 인덱싱된 파일 메타데이터 + 내용
    └─ NAS SMB                   ← 실시간 파일 접근
```

## 프로젝트 구조

```
nas-search/
├── src/
│   ├── config.py               # 환경설정
│   ├── crawler.py              # SMB NAS 크롤러
│   ├── indexer.py              # Elasticsearch 인덱싱
│   ├── searcher.py             # 검색 엔진 (파일명+내용 통합)
│   ├── mcp_server.py           # MCP 도구 서버
│   ├── content_extractor.py    # PDF/Office/HWP 내용 추출
│   ├── rag_system_optimized.py # RAG 벡터 검색
│   ├── claude_integration.py   # Claude AI 클라이언트
│   ├── gemini_integration.py   # Gemini AI 클라이언트
│   ├── ai_client.py            # AI 추상화 인터페이스
│   └── ai_factory.py           # AI 팩토리
├── frontend/
│   ├── src/
│   │   ├── views/ChatView.vue          # 자연어 채팅 UI
│   │   └── components/                 # 검색폼, 파일목록 등
│   ├── dist/                           # 빌드 결과물 (배포용)
│   └── package.json
├── app.py                      # Flask API 서버
├── run_crawl_index.py          # 크롤링 + 인덱싱 파이프라인
├── start_server.bat            # Flask 서버 실행
├── run_index.bat               # NAS 누적 인덱싱
├── run_index_reset.bat         # 전체 재인덱싱
├── .env                        # 환경변수 (Git 제외)
└── requirements.txt
```

## 빠른 시작

### 1. Flask 서버 실행
```
start_server.bat 더블클릭
```

### 2. 개발 모드 (프론트엔드)
```bash
cd frontend
npm run dev
# http://localhost:3000 접속
```

### 3. NAS 인덱싱
```
run_index.bat         # 누적 인덱싱 (새 파일만 추가)
run_index_reset.bat   # 전체 초기화 후 재인덱싱
```

## 배포

### Frontend 빌드
```bash
cd frontend
npm run build
# dist/ 폴더를 배포 서버에 복사
```

### IIS 설정 (배포 서버)
1. 사이트 루트 → `frontend/dist/`
2. ARR + URL Rewrite 설치
3. 인바운드 규칙 추가:
   - 패턴: `^api/(.*)`
   - 재작성 URL: `http://Flask서버IP:5000/api/{R:1}`

## 지원 파일 형식 (내용 검색)

| 형식 | 지원 |
|------|------|
| PDF | ✅ pdfplumber |
| DOCX | ✅ python-docx |
| XLSX | ✅ openpyxl |
| PPTX | ✅ python-pptx |
| HWP | ✅ olefile PrvText |
| TXT/CSV/JSON/MD | ✅ 직접 읽기 |
| 코드 (py/js/cpp 등) | ✅ 직접 읽기 |

## MCP 도구

| 도구 | 설명 |
|------|------|
| `search_files` | 파일명 + 내용 통합 검색 |
| `list_directory` | 디렉토리 탐색 |
| `get_file_info` | 파일 상세 정보 |
| `preview_file` | 파일 내용 미리보기 |

## AI 모델 선택

웹 UI 헤더에서 실시간 변경 가능:
- **Haiku** (기본) - 빠름, 저렴
- **Sonnet** - 고성능, 복잡한 요약에 적합

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.12 |
| NAS 접근 | smbprotocol (SMB) |
| 검색 엔진 | Elasticsearch 8.11.0 (Docker) |
| RAG | sentence-transformers 3.3.1 |
| AI | Claude API (Anthropic) |
| 웹 백엔드 | Flask |
| 프론트엔드 | Vue3 + Vuetify + Vite |

## 관련 문서

- [PROGRESS.md](PROGRESS.md) - 진행 상황 및 이슈
- [CONTEXT.md](CONTEXT.md) - 기술 컨텍스트 및 설계 결정
- [tasks.md](tasks.md) - 작업 목록

**최종 업데이트**: 2026-04-16
