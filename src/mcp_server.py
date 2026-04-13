"""
Model Context Protocol (MCP) 서버 구현
Claude와의 도구 기반 상호작용 제공
"""

import json
import logging
import time
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    logging.warning("anthropic library not installed. MCP features will be limited.")

from .config import Config
from .crawler import MultiNASCrawler
from .indexer import FileIndexer
from .searcher import FileSearcher


logger = logging.getLogger(__name__)


class NASSearchMCPServer:
    """
    NAS 검색 MCP 서버
    
    Claude와의 상호작용을 통해 NAS 파일 검색,
    디렉토리 탐색, 파일 정보 조회 기능 제공
    """
    
    def __init__(self):
        """MCP 서버 초기화"""
        Config.validate()
        
        self.crawler = MultiNASCrawler()
        self.crawler.connect_all()  # 모든 NAS에 연결
        
        self.indexer = FileIndexer()
        self.searcher = FileSearcher()
        
        # MCP 클라이언트 (선택사항)
        self.client = None
        
        logger.info("NAS Search MCP Server initialized")
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        MCP 도구 정의 반환
        
        Returns:
            List[Dict]: 도구 정의 리스트
        """
        return [
            {
                "name": "search_files",
                "description": "NAS에서 파일 검색",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색 쿼리 (파일명 또는 콘텐츠)"
                        },
                        "file_type": {
                            "type": "string",
                            "enum": ["document", "text", "image", "video", "audio", "archive", "code"],
                            "description": "파일 타입 필터 (선택사항)"
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 50,
                            "description": "최대 결과 수"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_directory",
                "description": "NAS 디렉토리 내용 조회",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "디렉토리 경로"
                        },
                        "recursive": {
                            "type": "boolean",
                            "default": False,
                            "description": "재귀적 탐색 여부"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_file_info",
                "description": "파일 상세 정보 조회",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "파일 경로"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "preview_file",
                "description": "텍스트 파일 미리보기",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "파일 경로"
                        },
                        "lines": {
                            "type": "integer",
                            "default": 20,
                            "description": "보여줄 라인 수"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]
    
    def search_files(
        self,
        query: str,
        file_type: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        파일 검색 (통합 검색)
        
        Args:
            query: 검색 쿼리 (파일명 또는 콘텐츠)
            file_type: 파일 타입 필터 (document, text, image, video, audio, archive, code)
            max_results: 최대 결과 수
        
        Returns:
            Dict: {
                "success": bool,
                "data": {
                    "files": [{name, path, size, modified, file_type, nas_name, score}, ...],
                    "total_count": int,
                    "elapsed_ms": float
                },
                "error": str (에러 시)
            }
        """
        start_time = time.time()
        
        try:
            logger.info(f"[search_files] query={query}, file_type={file_type}, max_results={max_results}")
            
            # Elasticsearch 고급 검색 호출
            results = self.searcher.search_advanced(
                name=query if query else None,
                file_type=file_type,
                max_results=max_results
            )
            
            # 결과 포매팅
            formatted_results = []
            for idx, result in enumerate(results):
                formatted_results.append({
                    "name": result.get("name", ""),
                    "path": result.get("path", ""),
                    "size": result.get("size", 0),
                    "modified": result.get("modified", ""),
                    "file_type": result.get("file_type", "other"),
                    "nas_name": result.get("nas_name", ""),
                    "score": 1.0 - (idx * 0.05)  # 순서 기반 스코어
                })
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[search_files] 결과: {len(formatted_results)}개 파일, {elapsed_ms:.2f}ms")
            
            return self._success_response({
                "files": formatted_results,
                "total_count": len(formatted_results),
                "elapsed_ms": round(elapsed_ms, 2)
            })
        
        except Exception as e:
            logger.error(f"[search_files] 에러: {str(e)}", exc_info=True)
            return self._error_response("SEARCH_ERROR", str(e))
    
    def list_directory(
        self,
        nas_name: str = "",
        path: str = "",
        recursive: bool = False,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        NAS 디렉토리 내용 조회
        
        Args:
            nas_name: NAS 이름 (예: "Local Test NAS", 기본값: 첫 번째 NAS)
            path: 상대 경로 (예: "Documents", "Photos/2026")
            recursive: 재귀 탐색 여부
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수
        
        Returns:
            Dict: {
                "success": bool,
                "data": {
                    "directories": [dir_names],
                    "files": [{name, path, size, modified, file_type}, ...],
                    "pagination": {page, page_size, total_items, total_pages}
                },
                "error": str (에러 시)
            }
        """
        start_time = time.time()
        
        try:
            # 경로 보안 검증
            if ".." in path:
                return self._error_response("INVALID_PATH", "Path traversal not allowed")
            
            # nas_name이 없으면 첫 번째 NAS 사용
            if not nas_name and self.crawler.crawlers:
                nas_name = self.crawler.crawlers[0].config.name
            
            logger.info(f"[list_directory] nas_name={nas_name}, path={path}, recursive={recursive}")
            
            # NAS 크롤러 찾기
            crawler = None
            for c in self.crawler.crawlers:
                if c.config.name == nas_name:
                    crawler = c
                    break
            
            if not crawler:
                # 첫 번째 NAS를 기본값으로 사용
                if self.crawler.crawlers:
                    crawler = self.crawler.crawlers[0]
                else:
                    return self._error_response("NAS_NOT_FOUND", f"NAS '{nas_name}' not found")
            
            # 파일 수집
            all_items = {"files": [], "directories": set()}
            
            for metadata in crawler.crawl(start_path=path, recursive=recursive):
                all_items["files"].append(metadata)
                
                # 디렉토리 추출 (부모 디렉토리)
                parent = os.path.dirname(metadata.path)
                if parent and parent != path:
                    dir_name = os.path.basename(parent)
                    if dir_name:
                        all_items["directories"].add(dir_name)
            
            # 페이지네이션 계산
            total_items = len(all_items["files"])
            total_pages = (total_items + page_size - 1) // page_size
            
            # 페이지 범위 검증
            if page < 1:
                page = 1
            if page > total_pages and total_items > 0:
                page = total_pages
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_files = all_items["files"][start_idx:end_idx]
            
            # 결과 포매팅
            formatted_files = []
            for metadata in paginated_files:
                formatted_files.append({
                    "name": metadata.name,
                    "path": metadata.path,
                    "size": metadata.size,
                    "modified": metadata.modified.isoformat(),
                    "file_type": metadata.file_type.value
                })
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[list_directory] 결과: {len(formatted_files)}개 항목, {elapsed_ms:.2f}ms")
            
            return self._success_response({
                "directories": sorted(list(all_items["directories"])),
                "files": formatted_files,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages
                },
                "elapsed_ms": round(elapsed_ms, 2)
            })
        
        except Exception as e:
            logger.error(f"[list_directory] 에러: {str(e)}", exc_info=True)
            return self._error_response("LIST_ERROR", str(e))
    
    def get_file_info(
        self,
        file_path: str,
        nas_name: str = "LOCAL"
    ) -> Dict[str, Any]:
        """
        파일 상세 정보 조회
        
        Args:
            file_path: 파일 경로
            nas_name: NAS 이름 (기본값: LOCAL)
        
        Returns:
            Dict: {
                "success": bool,
                "data": {
                    "name": str,
                    "path": str,
                    "size": int,
                    "modified": str (ISO format),
                    "file_type": str,
                    "nas_name": str,
                    "indexed": bool,
                    "indexed_time": str or null
                },
                "error": str (에러 시)
            }
        """
        start_time = time.time()
        
        try:
            # 경로 보안 검증
            if ".." in file_path:
                return self._error_response("INVALID_PATH", "Path traversal not allowed")
            
            logger.info(f"[get_file_info] file_path={file_path}, nas_name={nas_name}")
            
            # 1. Elasticsearch에서 먼저 찾기 (인덱싱된 경우)
            try:
                results = self.searcher.search_advanced(
                    name=os.path.basename(file_path),
                    nas_name=nas_name,
                    max_results=1
                )
                
                if results and results[0]["nas_name"] == nas_name:
                    hit = results[0]
                    elapsed_ms = (time.time() - start_time) * 1000
                    
                    return self._success_response({
                        "name": hit.get("name", ""),
                        "path": hit.get("path", file_path),
                        "size": hit.get("size", 0),
                        "modified": hit.get("modified", ""),
                        "file_type": hit.get("file_type", "other"),
                        "nas_name": hit.get("nas_name", nas_name),
                        "indexed": True,
                        "indexed_time": hit.get("indexed_time"),
                        "elapsed_ms": round(elapsed_ms, 2)
                    })
            except Exception as search_error:
                logger.warning(f"Elasticsearch search failed, trying filesystem: {search_error}")
            
            # 2. 파일 시스템에서 직접 정보 추출
            if not os.path.exists(file_path):
                return self._error_response("FILE_NOT_FOUND", f"File not found: {file_path}")
            
            try:
                stat_result = os.stat(file_path)
                
                # 파일 타입 결정 (임시 크롤러 사용)
                from .crawler import NASCrawler
                from .config import NASConfig
                
                temp_config = NASConfig(
                    host="local",
                    share="",
                    username="",
                    password="",
                    name=nas_name
                )
                temp_crawler = NASCrawler(temp_config)
                file_type_value = temp_crawler._get_file_type(file_path).value
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                return self._success_response({
                    "name": os.path.basename(file_path),
                    "path": file_path,
                    "size": stat_result.st_size,
                    "modified": datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
                    "file_type": file_type_value,
                    "nas_name": nas_name,
                    "indexed": False,
                    "indexed_time": None,
                    "elapsed_ms": round(elapsed_ms, 2)
                })
            
            except PermissionError:
                return self._error_response("PERMISSION_DENIED", f"Permission denied: {file_path}")
        
        except Exception as e:
            logger.error(f"[get_file_info] 에러: {str(e)}", exc_info=True)
            return self._error_response("INFO_ERROR", str(e))
    
    def preview_file(
        self,
        file_path: str,
        nas_name: str = "LOCAL",
        max_bytes: int = 1024
    ) -> Dict[str, Any]:
        """
        텍스트 파일 미리보기
        
        Args:
            file_path: 파일 경로
            nas_name: NAS 이름 (기본값: LOCAL)
            max_bytes: 최대 읽기 바이트 (기본값: 1KB)
        
        Returns:
            Dict: {
                "success": bool,
                "data": {
                    "name": str,
                    "content": str,
                    "is_text": bool,
                    "truncated": bool,
                    "size": int,
                    "encoding": str,
                    "lines": int
                },
                "error": str (에러 시)
            }
        """
        start_time = time.time()
        
        try:
            # 경로 보안 검증
            if ".." in file_path or file_path.startswith(".."):
                return self._error_response("INVALID_PATH", "Path traversal not allowed")
            
            logger.info(f"[preview_file] file_path={file_path}, max_bytes={max_bytes}")
            
            # 파일 존재 확인
            if not os.path.exists(file_path):
                return self._error_response("FILE_NOT_FOUND", f"File not found: {file_path}")
            
            # 파일 크기 확인
            file_size = os.path.getsize(file_path)
            if file_size > 5 * 1024 * 1024:  # 5MB 이상이면 처음 1KB만
                max_bytes = min(max_bytes, 1024)
            
            # 텍스트 파일 판단
            if not self._is_text_file(file_path):
                return self._error_response("UNSUPPORTED_TYPE", 
                    f"File type not supported for preview: {os.path.splitext(file_path)[1]}")
            
            # 인코딩 감지 및 읽기
            encoding = self._detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read(max_bytes)
            
            # 잘림 여부 판단
            truncated = file_size > max_bytes
            
            # 라인 수 계산
            lines = len(content.split('\n'))
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[preview_file] 성공: {lines} lines, truncated={truncated}, {elapsed_ms:.2f}ms")
            
            return self._success_response({
                "name": os.path.basename(file_path),
                "content": content,
                "is_text": True,
                "truncated": truncated,
                "size": file_size,
                "encoding": encoding,
                "lines": lines,
                "elapsed_ms": round(elapsed_ms, 2)
            })
        
        except PermissionError:
            return self._error_response("PERMISSION_DENIED", f"Permission denied: {file_path}")
        
        except Exception as e:
            logger.error(f"[preview_file] 에러: {str(e)}", exc_info=True)
            return self._error_response("PREVIEW_ERROR", str(e))
    
    def _is_text_file(self, file_path: str) -> bool:
        """텍스트 파일 판단"""
        text_extensions = {
            '.txt', '.log', '.md', '.json', '.yaml', '.yml', '.xml', '.csv',
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.go', '.rs',
            '.html', '.css', '.scss', '.sql', '.sh', '.bash', '.env',
            '.yml', '.properties', '.conf', '.config', '.ini'
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext in text_extensions
    
    def _detect_encoding(self, file_path: str) -> str:
        """파일 인코딩 감지"""
        encodings = ['utf-8', 'euc-kr', 'cp949', 'latin-1', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(512)  # 처음 512 바이트 읽기 시도
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        return 'utf-8'  # 기본값
    
    def _success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        성공 응답 포맷
        
        Args:
            data: 응답 데이터
        
        Returns:
            Dict: 표준화된 성공 응답
        """
        return {
            "success": True,
            "data": data
        }
    
    def _error_response(self, error_code: str, message: str) -> Dict[str, Any]:
        """
        에러 응답 포맷
        
        Args:
            error_code: 에러 코드
            message: 에러 메시지
        
        Returns:
            Dict: 표준화된 에러 응답
        """
        return {
            "success": False,
            "error": message,
            "error_code": error_code
        }
    
    def handle_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        도구 호출 처리
        
        Args:
            tool_name: 도구 이름
            tool_input: 도구 입력 파라미터
        
        Returns:
            Dict: 도구 실행 결과
        """
        logger.info(f"Tool call: {tool_name} with input {tool_input}")
        
        handlers = {
            "search_files": self.search_files,
            "list_directory": self.list_directory,
            "get_file_info": self.get_file_info,
            "preview_file": self.preview_file
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            return handler(**tool_input)
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }


# 글로벌 서버 인스턴스
nas_search_server = None


def initialize_server() -> NASSearchMCPServer:
    """
    MCP 서버 초기화
    
    Returns:
        NASSearchMCPServer: 초기화된 서버 인스턴스
    """
    global nas_search_server
    
    if nas_search_server is None:
        nas_search_server = NASSearchMCPServer()
    
    return nas_search_server
