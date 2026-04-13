# Phase 2: MCP 서버 도구 구현 상세 계획

## 📋 개요

Phase 1.5에서 완성한 `searcher.py`, `crawler.py`, `indexer.py`를 활용하여 MCP 프로토콜의 4개 도구를 구현합니다.

| 도구 | 목적 | 의존성 | 복잡도 |
|------|------|--------|--------|
| `search_files` | 파일 검색 | searcher.py | 중간 |
| `list_directory` | 경로 탐색 | crawler.py | 중간 |
| `get_file_info` | 파일 정보 | indexer.py, os.stat | 낮음 |
| `preview_file` | 미리보기 | os 모듈 | 높음 |

---

## 🔧 도구별 구현 상세

### 1️⃣ search_files (파일 검색)

#### 1-1. 메서드 서명
```python
def search_files(self, query: str, search_type: str = "advanced", 
                 filters: dict = None) -> dict:
    """
    Args:
        query: 검색 키워드
        search_type: "name" (파일명), "content" (내용), "advanced" (종합)
        filters: {
            "file_type": "archive" | "document" | ...,
            "nas_name": "NAS_1",
            "min_size": 1024,
            "max_size": 1073741824,
            "min_modified": "2026-01-01",
            "max_modified": "2026-04-11"
        }
    
    Returns:
        {
            "success": true,
            "data": {
                "files": [
                    {
                        "name": "file.zip",
                        "path": "D:\\Source\\file.zip",
                        "size": 251658240,
                        "modified": "2026-03-15T10:30:00",
                        "file_type": "archive",
                        "nas_name": "LOCAL",
                        "score": 0.95
                    },
                    ...
                ],
                "total_count": 12,
                "elapsed_ms": 45.23
            }
        }
    """
```

#### 1-2. 구현 전략
```python
# src/mcp_server.py - search_files 메서드

def search_files(self, query: str, search_type: str = "advanced", filters: dict = None) -> dict:
    try:
        start_time = time.time()
        
        if search_type == "name":
            # searcher.search_by_name(query) 호출
            results = self.searcher.search_by_name(query, size=100)
        
        elif search_type == "content":
            # searcher.search_by_content(query) 호출
            results = self.searcher.search_by_content(query, size=100)
        
        elif search_type == "advanced":
            # searcher.search_advanced() 호출 - 모든 필터 활용
            filters = filters or {}
            results = self.searcher.search_advanced(
                name=query,
                file_type=filters.get("file_type"),
                nas_name=filters.get("nas_name"),
                min_size=filters.get("min_size"),
                max_size=filters.get("max_size"),
                size=100
            )
        
        else:
            return self._error_response("INVALID_SEARCH_TYPE", f"Unknown search_type: {search_type}")
        
        # 결과 포매팅
        files = []
        for hit in results:
            files.append({
                "name": hit["name"],
                "path": hit["path"],
                "size": hit["size"],
                "modified": hit["modified"],
                "file_type": hit["file_type"],
                "nas_name": hit["nas_name"],
                "score": hit.get("score", 1.0)
            })
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return self._success_response({
            "files": files,
            "total_count": len(files),
            "elapsed_ms": round(elapsed_ms, 2)
        })
    
    except Exception as e:
        return self._error_response("SEARCH_ERROR", str(e))
```

#### 1-3. 테스트 케이스
```python
# test_mcp_search_files.py

def test_search_by_name():
    """파일명으로 검색"""
    result = server.search_files("zip", search_type="name")
    assert result["success"] == True
    assert len(result["data"]["files"]) == 2  # test_integration.py 기준

def test_search_advanced_with_filter():
    """필터를 포함한 고급 검색"""
    result = server.search_files(
        "",
        search_type="advanced",
        filters={"file_type": "archive"}
    )
    assert result["success"] == True
    assert len(result["data"]["files"]) == 5

def test_search_size_range():
    """크기 범위 검색"""
    result = server.search_files(
        "",
        search_type="advanced",
        filters={"min_size": 100*1024*1024, "max_size": 500*1024*1024}
    )
    assert result["success"] == True
    assert len(result["data"]["files"]) == 3

def test_search_empty_result():
    """검색 결과 없음"""
    result = server.search_files("nonexistent_file_12345", search_type="name")
    assert result["success"] == True
    assert len(result["data"]["files"]) == 0
```

---

### 2️⃣ list_directory (디렉토리 탐색)

#### 2-1. 메서드 서명
```python
def list_directory(self, nas_name: str, path: str = "", 
                   recursive: bool = False, page: int = 1) -> dict:
    """
    Args:
        nas_name: NAS 이름 (NAS_1, NAS_2 등)
        path: 상대 경로 ("Documents", "Photos/2026" 등)
        recursive: 재귀 탐색 여부
        page: 페이지 번호 (100개씩)
    
    Returns:
        {
            "success": true,
            "data": {
                "directories": ["Photos", "Documents"],
                "files": [
                    {
                        "name": "file.txt",
                        "path": "D:\\Source\\file.txt",
                        "size": 1024,
                        "modified": "2026-03-15T10:30:00",
                        "file_type": "text"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 100,
                    "total_items": 12,
                    "total_pages": 1
                }
            }
        }
    """
```

#### 2-2. 구현 전략
```python
def list_directory(self, nas_name: str, path: str = "", 
                   recursive: bool = False, page: int = 1) -> dict:
    try:
        # NAS 크롤러 찾기
        crawler = None
        for c in self.multi_crawler.crawlers:
            if c.nas_name == nas_name:
                crawler = c
                break
        
        if not crawler:
            return self._error_response("NAS_NOT_FOUND", f"NAS {nas_name} not found")
        
        # 경로 보안 검증 (상위 디렉토리 접근 방지)
        if ".." in path:
            return self._error_response("INVALID_PATH", "Path traversal not allowed")
        
        # 디렉토리 콘텐츠 수집
        all_files = []
        directories = set()
        
        for metadata in crawler.crawl(path, recursive=recursive):
            all_files.append(metadata)
            # 디렉토리 추출
            if metadata.path != path:
                parent_dir = os.path.dirname(metadata.path)
                if parent_dir and parent_dir != path:
                    directories.add(os.path.basename(parent_dir))
        
        # 페이지네이션
        page_size = 100
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_files = all_files[start_idx:end_idx]
        
        # 결과 포매팅
        files = []
        for metadata in paginated_files:
            files.append({
                "name": metadata.name,
                "path": metadata.path,
                "size": metadata.size,
                "modified": metadata.modified,
                "file_type": metadata.file_type
            })
        
        return self._success_response({
            "directories": sorted(list(directories)),
            "files": files,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": len(all_files),
                "total_pages": (len(all_files) + page_size - 1) // page_size
            }
        })
    
    except Exception as e:
        return self._error_response("LIST_ERROR", str(e))
```

#### 2-3. 테스트 케이스
```python
# test_mcp_list_directory.py

def test_list_root_directory():
    """루트 디렉토리 나열"""
    result = server.list_directory("LOCAL", "", recursive=False)
    assert result["success"] == True
    assert "files" in result["data"]
    assert result["data"]["pagination"]["total_items"] > 0

def test_list_with_pagination():
    """페이지네이션 테스트"""
    result1 = server.list_directory("LOCAL", "", page=1)
    result2 = server.list_directory("LOCAL", "", page=2)
    assert result1["success"] == True
```

---

### 3️⃣ get_file_info (파일 정보)

#### 3-1. 메서드 서명
```python
def get_file_info(self, file_path: str, nas_name: str) -> dict:
    """
    Args:
        file_path: 전체 파일 경로 또는 상대 경로
        nas_name: NAS 이름
    
    Returns:
        {
            "success": true,
            "data": {
                "name": "file.zip",
                "path": "D:\\Source\\file.zip",
                "size": 251658240,
                "modified": "2026-03-15T10:30:00",
                "file_type": "archive",
                "nas_name": "LOCAL",
                "indexed": true,
                "indexed_time": "2026-04-11T14:30:00"
            }
        }
    """
```

#### 3-2. 구현 전략
```python
def get_file_info(self, file_path: str, nas_name: str) -> dict:
    try:
        # 경로 검증
        if ".." in file_path:
            return self._error_response("INVALID_PATH", "Path traversal not allowed")
        
        # 1. Elasticsearch에서 먼저 찾기
        results = self.searcher.search_advanced(name=os.path.basename(file_path), size=1)
        
        if results and results[0]["nas_name"] == nas_name:
            hit = results[0]
            return self._success_response({
                "name": hit["name"],
                "path": hit["path"],
                "size": hit["size"],
                "modified": hit["modified"],
                "file_type": hit["file_type"],
                "nas_name": hit["nas_name"],
                "indexed": True,
                "indexed_time": hit.get("indexed_time", "")
            })
        
        # 2. 파일 시스템에서 직접 정보 추출
        try:
            stat_result = os.stat(file_path)
            file_type = self._detect_file_type(file_path)
            
            return self._success_response({
                "name": os.path.basename(file_path),
                "path": file_path,
                "size": stat_result.st_size,
                "modified": datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
                "file_type": file_type,
                "nas_name": nas_name,
                "indexed": False,
                "indexed_time": None
            })
        
        except FileNotFoundError:
            return self._error_response("FILE_NOT_FOUND", f"File not found: {file_path}")
    
    except Exception as e:
        return self._error_response("INFO_ERROR", str(e))
```

#### 3-3. 테스트 케이스
```python
# test_mcp_get_file_info.py

def test_get_indexed_file_info():
    """인덱싱된 파일 정보"""
    result = server.get_file_info("D:\\Source\\flutter.zip", "LOCAL")
    assert result["success"] == True
    assert result["data"]["indexed"] == True
    assert result["data"]["file_type"] == "archive"

def test_get_file_info_not_indexed():
    """인덱싱되지 않은 파일 정보"""
    # 임시 파일 생성 후 테스트
    test_file = "D:\\Source\\temp_test.txt"
    with open(test_file, "w") as f:
        f.write("test content")
    
    result = server.get_file_info(test_file, "LOCAL")
    assert result["success"] == True
    assert result["data"]["indexed"] == False
    
    os.remove(test_file)

def test_file_not_found():
    """파일 없음 처리"""
    result = server.get_file_info("D:\\Source\\nonexistent.txt", "LOCAL")
    assert result["success"] == False
    assert result["error_code"] == "FILE_NOT_FOUND"
```

---

### 4️⃣ preview_file (파일 미리보기) - 가장 복잡한 도구

#### 4-1. 메서드 서명
```python
def preview_file(self, file_path: str, nas_name: str, max_bytes: int = 1024) -> dict:
    """
    Args:
        file_path: 파일 경로
        nas_name: NAS 이름
        max_bytes: 최대 읽기 바이트 (기본 1KB)
    
    Returns:
        {
            "success": true,
            "data": {
                "name": "file.txt",
                "content": "Line 1\nLine 2\n...",
                "is_text": true,
                "truncated": false,
                "size": 2048,
                "encoding": "utf-8",
                "lines": 15
            }
        }
    """
```

#### 4-2. 구현 전략
```python
# 유틸리티 메서드들
def _is_text_file(self, file_path: str) -> bool:
    """텍스트 파일 판단"""
    text_extensions = {
        '.txt', '.log', '.md', '.json', '.yaml', '.yml', '.xml', '.csv',
        '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.go', '.rs',
        '.html', '.css', '.scss', '.sql', '.sh', '.bash', '.env'
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    return ext in text_extensions

def _detect_encoding(self, file_path: str) -> str:
    """파일 인코딩 감지"""
    encodings = ['utf-8', 'euc-kr', 'cp949', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(128)  # 첫 128글자 읽기 시도
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    return 'utf-8'  # 기본값

def preview_file(self, file_path: str, nas_name: str, max_bytes: int = 1024) -> dict:
    try:
        # 1. 보안 검증
        if ".." in file_path or file_path.startswith(".."):
            return self._error_response("INVALID_PATH", "Path traversal not allowed")
        
        # 2. 파일 존재 확인
        if not os.path.exists(file_path):
            return self._error_response("FILE_NOT_FOUND", f"File not found: {file_path}")
        
        # 3. 파일 크기 확인 (5MB 이상이면 처음 1KB만)
        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024:
            max_bytes = min(max_bytes, 1024)
        
        # 4. 텍스트 파일 판단
        if not self._is_text_file(file_path):
            return self._error_response("UNSUPPORTED_TYPE", 
                f"File type not supported for preview: {os.path.splitext(file_path)[1]}")
        
        # 5. 인코딩 감지 및 읽기
        encoding = self._detect_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read(max_bytes)
        
        # 6. 잘림 여부 판단
        truncated = file_size > max_bytes
        
        # 7. 라인 수 계산
        lines = len(content.split('\n'))
        
        return self._success_response({
            "name": os.path.basename(file_path),
            "content": content,
            "is_text": True,
            "truncated": truncated,
            "size": file_size,
            "encoding": encoding,
            "lines": lines
        })
    
    except PermissionError:
        return self._error_response("PERMISSION_DENIED", f"Permission denied: {file_path}")
    
    except Exception as e:
        return self._error_response("PREVIEW_ERROR", str(e))
```

#### 4-3. 테스트 케이스
```python
# test_mcp_preview_file.py

def test_preview_text_file():
    """텍스트 파일 미리보기"""
    result = server.preview_file("D:\\Source\\README.txt", "LOCAL")
    assert result["success"] == True
    assert result["data"]["is_text"] == True
    assert len(result["data"]["content"]) > 0

def test_preview_json_file():
    """JSON 파일 미리보기"""
    result = server.preview_file("D:\\Source\\config.json", "LOCAL")
    assert result["success"] == True
    assert result["data"]["encoding"] == "utf-8"

def test_preview_truncated():
    """큰 파일 자르기"""
    # 5MB+ 파일 생성
    large_file = "D:\\Source\\large_file.txt"
    with open(large_file, "w") as f:
        f.write("x" * (6 * 1024 * 1024))
    
    result = server.preview_file(large_file, "LOCAL", max_bytes=1024)
    assert result["success"] == True
    assert result["data"]["truncated"] == True
    assert len(result["data"]["content"]) <= 1024
    
    os.remove(large_file)

def test_preview_binary_file():
    """바이너리 파일 거부"""
    result = server.preview_file("D:\\Source\\flutter.zip", "LOCAL")
    assert result["success"] == False
    assert result["error_code"] == "UNSUPPORTED_TYPE"

def test_file_not_found():
    """파일 없음"""
    result = server.preview_file("D:\\Source\\nonexistent.txt", "LOCAL")
    assert result["success"] == False
    assert result["error_code"] == "FILE_NOT_FOUND"
```

---

## 🔨 응답 표준화

모든 도구는 다음 형식으로 응답합니다:

```python
def _success_response(self, data: dict) -> dict:
    return {
        "success": True,
        "data": data
    }

def _error_response(self, error_code: str, message: str) -> dict:
    return {
        "success": False,
        "error": message,
        "error_code": error_code
    }
```

### 에러 코드 정의
- `FILE_NOT_FOUND` - 파일이나 NAS를 찾을 수 없음
- `PERMISSION_DENIED` - 접근 권한 없음
- `INVALID_PATH` - 경로가 유효하지 않음 (경로 포함 공격)
- `TIMEOUT` - 작업 시간 초과
- `UNSUPPORTED_TYPE` - 파일 타입 미지원
- `SEARCH_ERROR` - 검색 중 오류
- `LIST_ERROR` - 디렉토리 나열 중 오류
- `INFO_ERROR` - 파일 정보 조회 중 오류
- `PREVIEW_ERROR` - 미리보기 중 오류
- `NAS_NOT_FOUND` - NAS를 찾을 수 없음
- `INVALID_SEARCH_TYPE` - 알 수 없는 검색 타입

---

## 📝 로깅 전략

```python
import logging

logger = logging.getLogger("nass")

# src/mcp_server.py 메서드 시작/끝에 추가
logger.info(f"[search_files] query={query}, type={search_type}, filters={filters}")
logger.info(f"[search_files] result={len(results)} files, elapsed={elapsed_ms}ms")
logger.error(f"[search_files] Error: {str(e)}", exc_info=True)
```

---

## 🧪 통합 테스트

```python
# test_mcp_integration.py

def test_full_workflow():
    """전체 워크플로우 테스트"""
    
    # 1. 검색
    result1 = server.search_files("zip", search_type="name")
    assert result1["success"]
    
    # 2. 첫 번째 파일 선택
    file_name = result1["data"]["files"][0]["name"]
    
    # 3. 파일 정보 조회
    result2 = server.get_file_info(file_name, "LOCAL")
    assert result2["success"]
    
    # 4. 텍스트 파일이면 미리보기
    if result2["data"]["file_type"] in ["text", "document"]:
        result3 = server.preview_file(file_name, "LOCAL")
        assert result3["success"]

def test_concurrent_requests():
    """동시성 테스트"""
    import threading
    
    results = []
    
    def search():
        results.append(server.search_files("zip"))
    
    threads = [threading.Thread(target=search) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert all(r["success"] for r in results)

def test_performance():
    """성능 검증"""
    import time
    
    start = time.time()
    result = server.search_files("zip")
    elapsed = (time.time() - start) * 1000
    
    assert elapsed < 100  # 100ms 이내
    assert result["data"]["elapsed_ms"] < 100
```

---

## ✅ 체크리스트

### 구현 체크리스트
- [ ] search_files 메서드 구현
- [ ] list_directory 메서드 구현
- [ ] get_file_info 메서드 구현
- [ ] preview_file 메서드 구현
- [ ] 응답 표준화 메서드 (_success_response, _error_response)
- [ ] 파일타입 감지 메서드 (_detect_file_type)
- [ ] 인코딩 감지 메서드 (_detect_encoding)
- [ ] 텍스트 파일 판단 메서드 (_is_text_file)

### 테스트 체크리스트
- [ ] test_mcp_search_files.py 작성 및 통과
- [ ] test_mcp_list_directory.py 작성 및 통과
- [ ] test_mcp_get_file_info.py 작성 및 통과
- [ ] test_mcp_preview_file.py 작성 및 통과
- [ ] test_mcp_integration.py 작성 및 통과 (통합 테스트)

### 문서화 체크리스트
- [ ] 도구별 README 업데이트
- [ ] PROGRESS.md 업데이트 (Phase 2 완료)
- [ ] API 스키마 문서 작성

---

## 📅 실행 순서

1. **search_files** 구현 및 테스트 (1-2시간)
   - searcher.py와 가장 간단한 통합
   - 기존 test_integration.py와 호환성 검증

2. **list_directory** 구현 및 테스트 (1시간)
   - crawler.py 활용
   - pagination 로직 추가

3. **get_file_info** 구현 및 테스트 (45분)
   - Elasticsearch + os.stat 폴백

4. **preview_file** 구현 및 테스트 (1-1.5시간)
   - 가장 복잡 (보안, 인코딩 감지, 파일타입 검증)

5. **응답 표준화** (30분)
   - 모든 도구에 공통 구조 적용
   - 에러 처리 통일

6. **통합 테스트 및 성능 검증** (1시간)
   - 모든 도구 함께 실행
   - 성능 벤치마크 (<100ms)

7. **문서화** (30분)
   - README 업데이트
   - PROGRESS.md 기록

**총 예상: 5.5-7시간**

---

## 🎯 Phase 2 완료 조건

- ✅ 4개 도구 모두 구현 완료
- ✅ 단위 테스트 100% 통과
- ✅ 통합 테스트 통과
- ✅ 성능 벤치마크 (<100ms) 달성
- ✅ 문서화 완료
- ✅ PROGRESS.md 업데이트

완료 후 Phase 3로 진행: Claude API 통합 테스트
