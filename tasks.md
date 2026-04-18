# 작업 항목 및 목표

## 완료된 작업 ✅

### Phase 1~6: 기초 구현
- [x] 프로젝트 구조, 환경 설정, 의존성 설치
- [x] Elasticsearch Docker 설치 및 연결
- [x] SMB 크롤러 구현 (smbclient.scandir 기반)
- [x] Elasticsearch 인덱싱 (배치, 누적)
- [x] RAG 벡터 인덱싱 (sentence-transformers)
- [x] MCP 4개 도구 구현
  - search_files: 파일명 + 내용 통합 검색
  - list_directory: 디렉토리 탐색
  - get_file_info: 파일 상세 정보
  - preview_file: ES content 우선 조회
- [x] Claude API 연동 (tool_use 패턴)
- [x] Gemini API 연동
- [x] AI 추상화 계층 (AIClient, AIClientFactory)

### Phase 7: SMB 크롤링 + 인덱싱 파이프라인
- [x] SMB 크롤링 (2,684개 파일)
- [x] ES 메타데이터 인덱싱 (2,684개)
- [x] RAG 벡터 인덱싱 (546개 텍스트 문서)
- [x] 파일 내용 추출 (PDF/DOCX/XLSX/PPTX/HWP/텍스트)

### Phase 8: 웹 UI + 배포
- [x] Vue3 + Vuetify 채팅 UI
- [x] Flask API 서버 (app.py)
- [x] 파일명 + 내용 통합 검색 수정
- [x] preview_file ES content 우선 조회
- [x] 메시지 전송 시 자동 스크롤
- [x] 모델 선택 드롭다운 (Haiku / Sonnet)
- [x] 도구 호출 로그 출력
- [x] Frontend Production 빌드
- [x] 실행 bat 파일 (start_server, run_index, run_index_reset)
- [x] LOCAL_NAS_PATH 주석처리 → SMB 모드 확인

---

## 진행 중 / 예정 작업

### MCP 표준 프로토콜 서버
- [ ] `mcp_server_stdio.py` 구현 (mcp SDK 사용)
- [ ] Claude Desktop 연결 테스트
- [ ] `~/.claude/settings.json` MCP 서버 등록

### 로컬 LLM 연동
- [ ] llama-cpp-python 설치
- [ ] `src/llama_cpp_integration.py` 구현
- [ ] AIFactory에 "local" 프로바이더 등록
- [ ] 프론트 모델 드롭다운에 "Gemma4 (로컬)" 옵션 추가

### 운영 편의성
- [ ] Windows 작업 스케줄러로 자동 인덱싱 등록
- [ ] 인덱싱 결과 알림 (이메일 or 로그)

---

## 차단 사항 (Blockers)

- 없음 (현재 정상 동작 중)

---

## 참고 문서

- [CONTEXT.md](CONTEXT.md): 기술 컨텍스트
- [PROGRESS.md](PROGRESS.md): 진행 상황
