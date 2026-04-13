# 사내 NAS 검색 MCP (Intranet NAS Search MCP)

## 프로젝트 개요

사내 NAS에 저장된 파일들을 Elasticsearch 기반 검색 엔진으로 효율적으로 검색할 수 있는 Model Context Protocol (MCP) 서버입니다.

**목표**: SMB 프로토콜로 여러 NAS에 접근하여 파일 메타데이터를 Elasticsearch에 인덱싱하고, Claude API 기반 MCP 도구로 제공

**아키텍처**: 풀스택 인덱싱 (Option 3)
- 백그라운드 크롤러로 NAS 파일 자동 탐색
- Elasticsearch로 고속 검색 (<100ms)
- MCP 도구로 Claude 통합 
- 웹 API를 통한 추가 통합 가능

## 프로젝트 구조

```
c:\Task\MCP\projects\intranet-nas-search\
├── src/                          # 핵심 소스 코드
│   ├── config.py                 # 환경설정 관리
│   ├── crawler.py                # SMB NAS 크롤러
│   ├── indexer.py                # Elasticsearch 인덱싱
│   ├── searcher.py               # 검색 엔진
│   └── mcp_server.py             # MCP 서버 구현
├── tests/                        # 테스트 코드
├── docs/                         # 프로젝트 문서
│   ├── MCP-INTERFACE.md          # MCP 도구 정의
│   ├── PYTHON-SMB-GUIDE.md       # SMB 학습 가이드
│   ├── OPTION2-VS-OPTION3.md     # 아키텍처 비교
│   ├── WEB-INTEGRATION.md        # 웹 통합 가이드
│   └── ...
├── data/                         # 데이터 저장소
├── requirements.txt              # Python 의존성 (21개 패키지)
├── .env.example                  # 환경변수 템플릿
├── CONTEXT.md                    # 프로젝트 컨텍스트
├── PROGRESS.md                   # 진행 상황 기록
├── tasks.md                      # 작업 항목 목록
└── README.md                     # 이 파일
```

## 기술 스택

| 항목 | 선택 | 버전 |
|------|------|------|
| 언어 | Python | 3.10+ |
| NAS 접근 | smbclient | 1.4.7 |
| 검색 엔진 | Elasticsearch | 8.11.0 |
| MCP SDK | anthropic | 0.29.0 |

## 주요 기능

### 현재 구현 ✅
- [x] 프로젝트 구조 및 설정 시스템
- [x] SMB 크롤러 기본 구조
- [x] Elasticsearch 인덱싱 (배치 처리 지원)
- [x] 고급 검색 (이름, 내용, 타입, 날짜, 크기 필터)
- [x] MCP 도구 정의 (4가지 도구)

### 개발 진행 중 🔄
- [ ] SMB 프로토콜 상세 구현
- [ ] 파일 콘텐츠 추출
- [ ] MCP 도구 메서드 완성
- [ ] 웹 백엔드 통합 (선택)

## 빠른 시작

### 1단계: 환경 설정

```bash
# Python 가상환경 생성
python -m venv venv

# 활성화 (Windows)
.\venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 환경변수 설정

```bash
# .env.example을 .env로 복사
copy .env.example .env

# .env 파일 편집 (NAS, Elasticsearch 정보 입력)
```

### 3단계: Elasticsearch 실행

```bash
# Docker로 실행
docker run -d -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

### 4단계: 테스트

```bash
# config 테스트
python -c "from src.config import Config; Config.validate()"
```

## 성능 특성

- **검색**: <100ms (Elasticsearch 최적화)
- **인덱싱**: 초당 100-500 파일
- **메모리**: ~2-5GB (기본 설정)

## 개발 타임라인

| Phase | 작업 | 상태 |
|-------|------|------|
| 0 | 구조 & 설정 | ✅ 완료 |
| 1 | SMB 크롤러 | 🔄 진행 중 |
| 2 | 인덱싱 & 검색 | 📋 대기 |
| 3-5 | MCP & 테스트 | 📋 대기 |

## 관련 문서

- [CONTEXT.md](CONTEXT.md) - 기술 컨텍스트
- [PROGRESS.md](PROGRESS.md) - 진행 상황
- [docs/MCP-INTERFACE.md](docs/MCP-INTERFACE.md) - MCP 도구 정의

**최종 업데이트**: 2026-04-11
