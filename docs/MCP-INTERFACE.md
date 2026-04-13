# MCP 인터페이스 설계 (초안)

## 개요

사내 NAS 검색 MCP는 Claude가 사내 파일을 검색, 조회, 탐색할 수 있는 인터페이스를 제공합니다.

## 인터페이스 구성

### 1. Tools (도구)

Claude가 호출할 수 있는 함수형 도구들입니다.

#### 1-1. `search_files`
**목적**: 파일명, 경로, 메타데이터로 파일 검색

```python
# 함수 시그니처 (예시)
def search_files(
    query: str,           # 검색어 (파일명, 일부 경로)
    nas_path: str,        # 검색 시작 경로 (예: /synology/nas1 또는 *전체)
    file_type: Optional[str] = None,  # 파일 확장자 필터 (예: .pdf, .doc)
    max_results: int = 50,  # 최대 결과 개수
    offset: int = 0       # 페이지네이션 오프셋
) -> SearchResult:       # 검색 결과
    """
    NAS에서 파일을 검색합니다.
    - 파일명 검색 (필수)
    - 선택적 필터: 파일 타입, NAS 경로, 결과 개수
    - 페이지네이션 지원
    """
```

**입출력 예시**
```
입력: 
  query = "보고서"
  nas_path = "*"
  file_type = ".pdf"
  max_results = 20

출력:
  {
    "results": [
      {
        "path": "/nas1/documents/2024_보고서.pdf",
        "name": "2024_보고서.pdf",
        "size": "2.5MB",
        "modified": "2026-04-10",
        "nas": "Synology NAS1"
      },
      ...
    ],
    "total_count": 45,
    "has_more": true
  }
```

---

#### 1-2. `list_directory`
**목적**: 특정 경로의 파일/폴더 목록 조회

```python
def list_directory(
    path: str,            # 조회 경로 (예: /nas1/documents)
    recursive: bool = False,  # 재귀적 조회 여부
    max_depth: int = 1    # 재귀 깊이
) -> DirectoryListing:
    """
    지정된 경로의 파일과 폴더를 나열합니다.
    - 경로 기반 조회 (SMB 경로)
    - 재귀 옵션지원
    - 폴더 구조 파악에 유용
    """
```

**입출력 예시**
```
입력:
  path = "/nas1/documents"
  recursive = false

출력:
  {
    "path": "/nas1/documents",
    "items": [
      {
        "name": "2024_보고서.pdf",
        "type": "file",
        "size": "2.5MB",
        "modified": "2026-04-10"
      },
      {
        "name": "monthly",
        "type": "directory",
        "item_count": 12
      }
    ]
  }
```

---

#### 1-3. `get_file_info`
**목적**: 특정 파일의 상세 정보 조회

```python
def get_file_info(
    path: str            # 파일 경로
) -> FileInfo:
    """
    파일의 상세 정보를 조회합니다.
    - 크기, 수정일, 소유자, 권한 등
    - 프리뷰 (텍스트 파일인 경우)
    """
```

**입출력 예시**
```
입력:
  path = "/nas1/documents/2024_보고서.pdf"

출력:
  {
    "name": "2024_보고서.pdf",
    "path": "/nas1/documents/2024_보고서.pdf",
    "size": "2.5MB",
    "type": "application/pdf",
    "modified": "2026-04-10T14:30:00Z",
    "created": "2026-03-15T09:00:00Z",
    "owner": "admin@company.com",
    "nas": "Synology NAS1"
  }
```

---

#### 1-4. `preview_file` (선택사항)
**목적**: 텍스트 파일의 미리보기

```python
def preview_file(
    path: str,
    lines: int = 50      # 미리보기 라인 수
) -> FilePreview:
    """
    텍스트 파일의 처음 N줄을 미리봅니다.
    - 텍스트 파일만 지원 (.txt, .md, .py, .json 등)
    - 바이너리 파일은 매직 바이트 표시
    """
```

---

### 2. Resources (리소스)

Claude가 참고할 수 있는 정적/동적 정보입니다.

#### 2-1. `nas://list`
**설명**: 접근 가능한 모든 NAS와 경로 목록

```json
{
  "uri": "nas://list",
  "description": "접근 가능한 NAS 목록 및 주요 경로",
  "content": "# 사내 NAS 목록\n\n## Synology NAS1\n- 경로: /nas1\n- 주요 폴더: documents, media, projects\n\n## NAS2 (기타)\n- 경로: /nas2\n- 주요 폴더: archive, shared"
}
```

#### 2-2. `nas://paths/{nas_name}`
**설명**: 특정 NAS의 폴더 구조 (캐시됨)

```json
{
  "uri": "nas://paths/synology",
  "description": "Synology NAS의 폴더 구조",
  "content": "[폴더 구조 트리]"
}
```

---

### 3. Prompts (프롬프트 템플릿)

Claude가 쉽게 사용할 수 있는 프롬프트 템플릿입니다.

#### 3-1. `search_by_date`
**설명**: 날짜 범위로 파일 검색

```
프롬프트: "2026년 3월에 만든 PDF 파일을 찾아줘"

내부 실행:
1. search_files(query="*.pdf", modified_after="2026-03-01", modified_before="2026-03-31")
```

#### 3-2. `find_recent_files`
**설명**: 최근 수정된 파일 찾기

```
프롬프트: "지난 일주일 동안 수정된 파일들을 보여줘"

내부 실행:
1. search_files(query="*", modified_after=<7일전>, sort="modified_desc")
```

---

## MCP 인터페이스 최종 구조

| 카테고리 | 항목 | 상태 | 우선순위 |
|---------|------|------|---------|
| **Tools** | search_files | ✅ 필수 | 1️⃣ |
| | list_directory | ✅ 필수 | 1️⃣ |
| | get_file_info | ✅ 필수 | 1️⃣ |
| | preview_file | ⏳ 선택 | 2️⃣ |
| **Resources** | nas://list | ✅ 필수 | 2️⃣ |
| | nas://paths/{name} | ⏳ 선택 | 3️⃣ |
| **Prompts** | search_by_date | ⏳ 선택 | 3️⃣ |
| | find_recent_files | ⏳ 선택 | 3️⃣ |

---

## 아키텍처별 인터페이스 차이

### 옵션 1 (단순 패스스루)
- ✅ 모든 도구 직접 NAS 조회
- ⚠️ 대량 요청 시 느림

### 옵션 2 (캐시 계층) ⭐ 추천
- ✅ search_files/list_directory: 캐시 우선 조회
- ⚠️ 최대 캐시 나이 파라미터 추가 가능
- ✅ 응답 속도 개선

### 옵션 3 (풀스택 캐싱)
- ✅ search_files: 인덱스 기반 초고속 검색
- ✅ 파일 내용 전문 검색 가능
- ⚠️ 인덱싱 지연 (크롤러 종속)

---

## 다음 단계

1. [ ] 선택한 아키텍처 확정
2. [ ] 각 Tool의 에러 처리 정의
3. [ ] 인증 & 권한 관리 설계
4. [ ] 초기 프로토타입 구현 (search_files + list_directory)
