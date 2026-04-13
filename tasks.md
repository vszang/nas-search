# 작업 항목 및 목표

## 전체 프로젝트 타임라인

| 단계 | 설명 | 예상 기간 |
|------|------|---------|
| 1️⃣ 계획 | 요구사항 분석, 기술 스택 결정, 아키텍처 설계 | 1-2일 |
| 2️⃣ 기초 구현 | MCP 서버 기본 구조, NAS 연결 | 2-3일 |
| 3️⃣ 검색 기능 | 파일 검색 도구 구현 | 2-3일 |
| 4️⃣ 통합 및 테스트 | 통합 테스트, 성능 최적화 | 1-2일 |
| 5️⃣ 배포 | 배포 자동화, 문서 작성 | 1일 |

## 현재 진행 단계: Phase 1.5 (기초 구현 준비) - 구조 완성 후 개발 시작 단계

### 1단계: 계획 및 설계

#### 요구사항 분석
- [ ] **1-1**: 사내 NAS 정보 수집
  - NAS 위치, 프로토콜, 접근 방식 확인
  - 저장된 데이터 유형 및 규모 파악
  - 보안 정책 확인

- [ ] **1-2**: 사용 사례(Use Case) 정의
  - 주요 검색 시나리오 정의
  - 워크플로우 정의

#### 기술 스택 결정
- [x] **1-3**: 프로그래밍 언어 선택 ✅
  - 선택: Python 3.10+
  - 이유: 교육 목적, 이식성, MCP SDK 성숙도

- [x] **1-4**: NAS 연결 방식 결정 ✅
  - 선택: Python SMB 라이브러리 (옵션 B)
  - 후보 라이브러리: `smbclient`, `pysmb`
  - 이유: 여러 NAS 관리, 이식성, 유연한 인증

#### 아키텍처 설계
- [x] **1-5**: MCP 한정(Scoping) 및 인터페이스 정의 🔄 진행중
  - 참고: [docs/MCP-INTERFACE.md](../docs/MCP-INTERFACE.md)
  - Tools: search_files, list_directory, get_file_info, preview_file
  - Resources: nas://list, nas://paths/{name}
  - Prompts: search_by_date, find_recent_files

- [x] **1-6**: 고급 설계 검토 ✅
  - 에러 처리 및 타임아웃
  - 성능 최적화 계획 (배치 처리, 비동기 크롤링)

### Phase 1.5: 기초 구현 준비 ✅

- [x] **1.5-1**: 프로젝트 구조 및 모듈 기본 구성 ✅
  - src/, tests/, data/ 폴더 생성
  - config.py, crawler.py, indexer.py, searcher.py, mcp_server.py 작성
  
- [x] **1.5-2**: requirements.txt 작성 ✅
  - smbclient, elasticsearch, anthropic, pytest 등 21개 패키지
  
- [ ] **1.5-3**: 개발 환경 구성
  - Python 가상환경 생성 및 활성화
  - pip install -r requirements.txt
  - Elasticsearch 설치 (Docker 또는 Windows native)
  
- [ ] **1.5-4**: 환경변수 설정 및 테스트
  - .env 파일 작성 (NAS, Elasticsearch 정보)
  - config.py 실행 테스트

### Phase 2: MCP 서버 도구 구현

#### 2-1: search_files 도구 구현 (파일 검색) ✅
- [x] **2-1-1**: 메서드 서명 정의 ✅
- [x] **2-1-2**: searcher.py 통합 ✅
- [x] **2-1-3**: 결과 포매팅 ✅
- [x] **2-1-4**: 단위 테스트 (test_mcp_search_files.py) ✅
  - 12/12 테스트 통과
  - 성능: 20-53ms (<100ms 달성)
  - 모든 필터링 기능 검증

#### 2-2: list_directory 도구 구현 (경로 탐색)
- [ ] **2-2-1**: 메서드 서명 정의
  - 입력: nas_name, path (선택), recursive (bool)
  - 출력: { directories: [], files: [], page_info: {} }
  
- [ ] **2-2-2**: crawler.py 통합
  - MultiNASCrawler 사용
  - 특정 NAS의 파일만 필터링
  - 재귀/비재귀 모드 지원
  
- [ ] **2-2-3**: 페이지네이션 (대량 파일 처리)
  - 최대 100개씩 반환
  - 페이지 토큰 제공
  
- [ ] **2-2-4**: 단위 테스트 (test_mcp_list_directory.py)
  - NAS 목록 조회
  - 특정 경로의 파일 나열
  - 재귀 옵션 테스트
  - 페이지네이션 테스트

#### 2-3: get_file_info 도구 구현 (파일 정보)
- [ ] **2-3-1**: 메서드 서명 정의
  - 입력: file_path, nas_name
  - 출력: { path, name, size, modified_time, file_type, nas_name, indexed: bool }
  
- [ ] **2-3-2**: Elasticsearch 쿼리
  - 파일 경로로 정확히 일치하는 문서 조회
  - 인덱스되지 않은 파일은 크롤러에서 정보 추출
  
- [ ] **2-3-3**: 폴백 처리
  - Elasticsearch에 없으면 os.stat() 사용
  - 권한 오류 처리
  
- [ ] **2-3-4**: 단위 테스트 (test_mcp_get_file_info.py)
  - 특정 파일 정보 조회
  - 마지막 수정시간 검증
  - 파일타입 분류 검증
  - 존재하지 않는 파일 처리

#### 2-4: preview_file 도구 구현 (파일 미리보기)
- [ ] **2-4-1**: 메서드 서명 정의
  - 입력: file_path, nas_name, max_bytes (기본 1024)
  - 출력: { content: str, is_text: bool, truncated: bool, encoding: str }
  
- [ ] **2-4-2**: 파일 타입 판단
  - 텍스트 파일만 읽기 (txt, log, md, json, csv, xml, py, js, java, c, etc)
  - 바이너리 파일 거부
  
- [ ] **2-4-3**: 인코딩 감지 및 읽기
  - 기본: UTF-8
  - 폴백: EUC-KR, CP949
  - 읽기 실패 시 "preview not available" 반환
  
- [ ] **2-4-4**: 보안 처리
  - 파일 크기 제한 (5MB 이상이면 처음 1KB만)
  - 경로 조회로 접근 허용 파일 확인
  - 상위 디렉토리(..) 경로 진입 방어
  
- [ ] **2-4-5**: 단위 테스트 (test_mcp_preview_file.py)
  - 텍스트 파일 미리보기 (txt 파일)
  - JSON 파일 미리보기
  - 바이너리 파일 거부 확인
  - 큰 파일 자르기 확인
  - 존재하지 않는 파일 처리

#### 2-5: MCP 프로토콜 응답 표준화
- [ ] **2-5-1**: 모든 도구의 반환값 형식 통일
  - Success: { success: true, data: {...} }
  - Error: { success: false, error: str, error_code: str }
  
- [ ] **2-5-2**: 에러 코드 정의
  - "FILE_NOT_FOUND", "PERMISSION_DENIED", "INVALID_PATH", "TIMEOUT", "UNSUPPORTED_TYPE"
  
- [ ] **2-5-3**: 로깅 추가
  - 각 도구 호출 로깅 (요청, 응답, 소요시간)
  - 에러 로깅

#### 2-6: 통합 테스트
- [ ] **2-6-1**: test_mcp_integration.py 작성
  - 4개 도구를 순서대로 호출
  - 서로 다른 시나리오 테스트
  - 동시성 테스트 (threading)
  
- [ ] **2-6-2**: 성능 검증
  - 각 도구별 응답시간 < 100ms 확인
  - 메모리 사용량 모니터링
  
- [ ] **2-6-3**: 에러 복구 테스트
  - 잘못된 경로 입력
  - 타임아웃 상황
  - 연결 끊김

#### 2-7: 문서화
- [ ] **2-7-1**: 도구별 README 작성
  - 각 도구의 입출력 스키마
  - 사용 예시
  - 제한사항
  
- [ ] **2-7-2**: PROGRESS.md 업데이트
  - Phase 2 완료 기록
  - 다음 단계 (Phase 3) 준비

---

## Phase 2 일정

| 작업 | 예상 기간 | 담당 |
|------|---------|------|
| 2-1: search_files | 1-2시간 | Agent |
| 2-2: list_directory | 1시간 | Agent |
| 2-3: get_file_info | 45분 | Agent |
| 2-4: preview_file | 1-1.5시간 | Agent |
| 2-5: 응답 표준화 | 30분 | Agent |
| 2-6: 통합 테스트 | 1시간 | Agent |
| 2-7: 문서화 | 30분 | Agent |
| **합계** | **5.5-7시간** | |

---

## 작업 우선순위

### 높음 (필수)
1. NAS 정보 수집 및 연결 테스트 (1-1)
2. 기술 스택 선택 및 검증 (1-3, 1-4)
3. MCP 인터페이스 정의 (1-5)

### 중간 (권장)
4. 아키텍처 상세 설계 (1-6)
5. 초기 프로토타입 구현 (2단계)

### 낮음 (추후)
6. 성능 최적화
7. 배포 자동화

## 차단 사항 (Blockers)

- ⚠️ 사내 NAS 정보 (위치, 프로토콜, 접근 권한) 필수 - **1-1 완료 후 진행 가능**

## 참고 문서

- [CONTEXT.md](CONTEXT.md): 기술 컨텍스트
- [PROGRESS.md](PROGRESS.md): 진행 상황
