# 진행 상황 기록

## 진행 상황 요약

| 날짜 | 작업 | 완료 여부 | 비고 |
|------|------|---------|------|
| 2026-04-11 | 프로젝트 구조 및 초기 문서 생성 | ✅ | 루트 CLAUDE.md, 프로젝트 폴더 구조 설정 |
| 2026-04-12 | Phase 2~6 구현 | ✅ | MCP 4개 도구, AI 클라이언트, E2E 테스트 |
| 2026-04-13 | 환경 구축 및 NAS 연결 | ✅ | ES Docker, venv, RAG 버그 수정, SMB 연결 확인 |
| 2026-04-14 | SMB 크롤링 + 인덱싱 파이프라인 + Office/HWP 추출 | ✅ | 2,684개 파일 인덱싱, PDF/DOCX/XLSX/PPTX/HWP 내용 추출 |
| 2026-04-14 | Claude AI 연동 테스트 | ✅ | claude-haiku-4-5 기본 모델, 자연어 검색 동작 확인 |
| 2026-04-15 | 검색/미리보기 버그 수정 + 웹 UI 개선 | ✅ | 파일명+내용 통합검색, ES content 조회, 스크롤 자동이동 |
| 2026-04-15 | 배포 준비 | ✅ | Frontend 빌드, bat 파일 생성, 모델 선택 UI |
| 2026-04-16 | NAS 전체 재인덱싱 | ✅ | LOCAL_NAS_PATH 주석처리, SMB 직접 크롤링 확인 |

---

## 최종 완성 상태 (2026-04-16)

### 전체 아키텍처
```
브라우저 (Vue3)
    ↓ HTTP /api/*
Flask (app.py, port 5000)
    ↓
ClaudeNASSearchClient (claude_integration.py)
    ↓ tool_use
NASSearchMCPServer (mcp_server.py)
    ↓
Elasticsearch (port 9200) ← 인덱싱된 파일 메타데이터 + 내용
NAS SMB (192.168.0.101)  ← 실시간 파일 접근
```

### 구현 완료 목록

#### 크롤링 & 인덱싱
- ✅ SMB 크롤링 (`crawler.py`) - smbclient.scandir 기반 재귀 탐색
- ✅ Elasticsearch 배치 인덱싱 (`indexer.py`) - 2,684개 파일
- ✅ RAG 벡터 인덱싱 (`rag_system_optimized.py`) - 546개 텍스트 문서
- ✅ 파일 내용 추출 (`content_extractor.py`) - PDF/DOCX/XLSX/PPTX/HWP/텍스트

#### 내용 추출 현황 (재인덱싱 결과)
| 형식 | 추출 수 |
|------|--------|
| .cpp | 385 |
| .txt | 82 |
| .xlsx | 34 |
| .docx | 33 |
| .pptx | 24 |
| .pdf | 17 |
| .md | 9 |
| .hwp | 6 |
| 기타 | 10 |

#### MCP 도구
- ✅ `search_files` - 파일명 + 내용 통합 검색 (OR, 파일명 가중치 2배)
- ✅ `list_directory` - 디렉토리 탐색, 페이지네이션
- ✅ `get_file_info` - 파일 상세 정보
- ✅ `preview_file` - ES content 우선 조회 → 로컬 직접 읽기 → SMB 실시간 추출

#### AI 통합
- ✅ Claude API 연동 (`claude_integration.py`)
- ✅ 기본 모델: `claude-haiku-4-5-20251001` (빠름/저렴)
- ✅ 선택 모델: `claude-sonnet-4-6` (고성능)
- ✅ 프론트에서 모델 선택 가능

#### 웹 UI (Vue3 + Vuetify)
- ✅ 자연어 채팅 인터페이스 (`ChatView.vue`)
- ✅ 파일 검색 폼 (`SearchForm.vue`)
- ✅ 파일 상세 다이얼로그 (`FileDetailDialog.vue`)
- ✅ 디렉토리 탐색기 (`DirectoryExplorer.vue`)
- ✅ 메시지 전송 시 자동 스크롤
- ✅ 모델 선택 드롭다운 (헤더)
- ✅ Production 빌드 완료 (`frontend/dist/`)

#### 배포 파일
- ✅ `start_server.bat` - Flask 서버 실행
- ✅ `run_index.bat` - NAS 누적 인덱싱
- ✅ `run_index_reset.bat` - 전체 재인덱싱 (확인 프롬프트 포함)

---

## 배포 구성

### 현재 VM (Flask 실행)
- Flask 서버: `start_server.bat` 실행
- Elasticsearch: Docker 컨테이너 (port 9200)
- NAS 인덱싱: `run_index.bat` 필요 시 실행

### 배포 서버 (IIS)
- 사이트 루트: `frontend/dist/`
- URL Rewrite: `/api/*` → Flask VM 내부 IP:5000
- ARR 프록시 사용 설정 필요

### 인덱싱 주기
- 수동 실행: `run_index.bat` (누적) 또는 `run_index_reset.bat` (초기화)
- NAS 파일 추가 시 `run_index.bat` 실행으로 반영

---

## 알려진 이슈 / 개선 사항

- HWP 전체 본문 추출 미지원 (현재 PrvText 미리보기 약 700자만 가능)
- 작업 스케줄러를 통한 자동 인덱싱 미설정 (수동 실행)
- 인덱싱되지 않은 파일(ES content 없음)은 preview_file 실패 가능

---

## 다음 계획

- [ ] MCP 표준 프로토콜 서버 구현 (`mcp_server_stdio.py`) - Claude Desktop 연결용
- [ ] llama-cpp-python 기반 로컬 Gemma4 모델 연동
- [ ] 작업 스케줄러 자동 인덱싱 설정
