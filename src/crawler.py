"""
NAS 크롤러 모듈
SMB 프로토콜 또는 로컬 파일시스템을 통한 NAS 파일 시스템 접근 및 메타데이터 추출
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, AsyncIterator, Iterator
from pathlib import Path
from enum import Enum

try:
    import smbclient
    import smbclient.shutil
except ImportError:
    smbclient = None

from .config import NASConfig, Config


logger = logging.getLogger(__name__)


class FileType(Enum):
    """파일 타입 분류"""
    DOCUMENT = "document"      # PDF, DOC, DOCX, PPTX, XLS, XLSX
    TEXT = "text"              # TXT, LOG, CSV, JSON, XML
    IMAGE = "image"            # JPG, PNG, GIF, BMP
    VIDEO = "video"            # MP4, AVI, MOV, MKV
    AUDIO = "audio"            # MP3, WAV, FLAC
    ARCHIVE = "archive"        # ZIP, RAR, 7Z
    CODE = "code"              # PY, JS, JAVA, CPP, CS
    OTHER = "other"            # 기타


@dataclass
class FileMetadata:
    """파일 메타데이터"""
    path: str               # 전체 경로
    name: str               # 파일명
    size: int               # 바이트 단위 크기
    modified: datetime      # 수정 시간
    file_type: FileType     # 파일 타입
    nas_name: str          # NAS 이름
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "modified": self.modified.isoformat(),
            "file_type": self.file_type.value,
            "nas_name": self.nas_name
        }


class NASCrawler:
    """
    NAS 크롤러 (SMB 또는 로컬 경로 지원)
    
    SMB 프로토콜을 통한 NAS 접근 또는 로컬 파일시스템 접근
    (테스트용도로 로컬 경로도 지원)
    """
    
    def __init__(self, config: NASConfig, index: int = 1):
        self.config = config
        self.index = index
        self.client = None
        self._file_type_map = self._build_file_type_map()
        self.is_local_path = False  # 로컬 경로 여부
    
    def _build_file_type_map(self) -> dict:
        """확장자별 파일 타입 매핑"""
        return {
            # 문서
            "pdf": FileType.DOCUMENT,
            "doc": FileType.DOCUMENT,
            "docx": FileType.DOCUMENT,
            "pptx": FileType.DOCUMENT,
            "ppt": FileType.DOCUMENT,
            "xls": FileType.DOCUMENT,
            "xlsx": FileType.DOCUMENT,
            
            # 텍스트
            "txt": FileType.TEXT,
            "log": FileType.TEXT,
            "csv": FileType.TEXT,
            "json": FileType.TEXT,
            "xml": FileType.TEXT,
            "sql": FileType.TEXT,
            
            # 이미지
            "jpg": FileType.IMAGE,
            "jpeg": FileType.IMAGE,
            "png": FileType.IMAGE,
            "gif": FileType.IMAGE,
            "bmp": FileType.IMAGE,
            
            # 비디오
            "mp4": FileType.VIDEO,
            "avi": FileType.VIDEO,
            "mov": FileType.VIDEO,
            "mkv": FileType.VIDEO,
            
            # 오디오
            "mp3": FileType.AUDIO,
            "wav": FileType.AUDIO,
            "flac": FileType.AUDIO,
            
            # 압축
            "zip": FileType.ARCHIVE,
            "rar": FileType.ARCHIVE,
            "7z": FileType.ARCHIVE,
            
            # 코드
            "py": FileType.CODE,
            "js": FileType.CODE,
            "java": FileType.CODE,
            "cpp": FileType.CODE,
            "cs": FileType.CODE,
        }
    
    def connect(self) -> bool:
        """
        NAS에 접속 (SMB 또는 로컬 경로)

        Returns:
            bool: 성공 여부
        """
        try:
            # 로컬 경로 확인
            local_path = os.getenv(f"LOCAL_NAS_PATH_{self.index}")
            if local_path and os.path.isdir(local_path):
                logger.info(f"Using local path: {local_path}")
                self.is_local_path = True
                self.local_path = local_path
                return True

            # SMB 연결 시도
            if smbclient is None:
                logger.error("smbclient not installed. Run: pip install smbprotocol")
                return False

            logger.info(f"Connecting to NAS: {self.config.name} ({self.config.host})")

            smbclient.register_session(
                self.config.host,
                username=self.config.username,
                password=self.config.password,
            )

            # 연결 확인: 공유 루트 접근 테스트
            smb_root = f"\\\\{self.config.host}\\{self.config.share}"
            smbclient.listdir(smb_root)

            self.smb_base = smb_root
            logger.info(f"Successfully connected to {self.config.name} ({smb_root})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to NAS {self.config.name}: {str(e)}")
            return False
    
    def _get_file_type(self, filename: str) -> FileType:
        """파일명으로 파일 타입 결정"""
        ext = Path(filename).suffix.lower().lstrip(".")
        return self._file_type_map.get(ext, FileType.OTHER)
    
    def _smb_crawl(self, smb_path: str, recursive: bool = True) -> Iterator[FileMetadata]:
        """
        SMB 경로를 재귀적으로 탐색하며 파일 메타데이터 반환

        Args:
            smb_path: UNC 경로 (\\\\host\\share\\folder)
            recursive: 재귀 탐색 여부
        """
        try:
            entries = smbclient.scandir(smb_path)
        except Exception as e:
            logger.warning(f"Cannot list SMB directory {smb_path}: {str(e)}")
            return

        for entry in entries:
            name = entry.name

            # 숨김 파일/폴더 및 시스템 폴더 제외
            if name.startswith('.') or name.lower() in ('#recycle', '@eadir', '#snapshot'):
                continue

            entry_path = f"{smb_path}\\{name}"

            try:
                if entry.is_dir(follow_symlinks=False):
                    if recursive:
                        yield from self._smb_crawl(entry_path, recursive=recursive)
                else:
                    stat = entry.stat(follow_symlinks=False)
                    metadata = self.extract_metadata(entry_path, stat_result=stat)
                    if metadata:
                        yield metadata
            except Exception as e:
                logger.warning(f"Error processing SMB entry {entry_path}: {str(e)}")

    def extract_metadata(self, file_path: str, stat_result=None) -> Optional[FileMetadata]:
        """
        파일 메타데이터 추출
        
        Args:
            file_path: 파일 경로
            stat_result: SMB stat 결과 (로컬파일일 때는 os.stat 결과)
        
        Returns:
            FileMetadata 또는 None
        """
        try:
            if stat_result is None and self.is_local_path:
                # 로컬 경로인 경우 os.stat 사용
                stat_result = os.stat(file_path)
            
            modified_time = datetime.fromtimestamp(stat_result.st_mtime) if stat_result else datetime.now()
            
            return FileMetadata(
                path=file_path,
                name=Path(file_path).name,
                size=stat_result.st_size if stat_result else 0,
                modified=modified_time,
                file_type=self._get_file_type(file_path),
                nas_name=self.config.name
            )
        except Exception as e:
            logger.error(f"Failed to extract metadata for {file_path}: {str(e)}")
            return None
    
    def crawl(self, start_path: str = "/", recursive: bool = True) -> Iterator[FileMetadata]:
        """
        NAS 파일 시스템 크롤링
        
        Args:
            start_path: 시작 경로 (기본값: 공유 루트)
            recursive: 재귀적 탐색 여부
        
        Yields:
            FileMetadata: 발견된 파일의 메타데이터
        """
        # start_path 우선순위: 인자 > config.start_path > 기본값("/")
        if start_path == "/" and self.config.start_path:
            start_path = self.config.start_path

        logger.info(f"Starting crawl of {self.config.name} from '{start_path}'")

        if self.is_local_path:
            # 로컬 경로 크롤링
            base_path = getattr(self, 'local_path', None)
            if not base_path:
                return

            # start_path가 지정된 경우 해당 하위 폴더만 탐색
            if start_path and start_path != "/":
                base_path = os.path.join(base_path, start_path.lstrip("/\\"))
                if not os.path.isdir(base_path):
                    logger.error(f"Start path not found: {base_path}")
                    return

            try:
                for root, dirs, files in os.walk(base_path):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        try:
                            metadata = self.extract_metadata(file_path)
                            if metadata:
                                yield metadata
                        except Exception as e:
                            logger.warning(f"Error processing {file_path}: {str(e)}")
                    
                    # 재귀 탐색 안 하면 종료
                    if not recursive:
                        break
                    
                    # 숨김 폴더 제외
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
            except Exception as e:
                logger.error(f"Local path crawl failed: {str(e)}")
        else:
            # SMB 크롤링: \\host\share[\start_path]
            smb_base = getattr(self, 'smb_base', f"\\\\{self.config.host}\\{self.config.share}")
            if start_path and start_path != "/":
                sub = start_path.strip('/\\').replace('/', '\\')
                smb_base = f"{smb_base}\\{sub}"

            logger.info(f"SMB crawl path: {smb_base}")
            yield from self._smb_crawl(smb_base, recursive=recursive)


class MultiNASCrawler:
    """
    여러 NAS를 관리하는 크롤러
    
    여러 개의 NAS에 동시에 크롤링 작업 수행
    """
    
    def __init__(self):
        Config.load_nas_configs()
        self.crawlers = [
            NASCrawler(config, index=i) for i, config in enumerate(Config.NAS_CONFIGS, 1)
        ]
    
    def connect_all(self) -> int:
        """
        모든 NAS에 연결
        
        Returns:
            int: 성공한 연결 수
        """
        success_count = 0
        for crawler in self.crawlers:
            if crawler.connect():
                success_count += 1
        
        logger.info(f"Connected to {success_count}/{len(self.crawlers)} NAS systems")
        return success_count
    
    def crawl_all(self, recursive: bool = True) -> List[FileMetadata]:
        """
        모든 NAS 크롤링 (동기 방식)
        
        Args:
            recursive: 재귀적 탐색 여부
        
        Returns:
            List[FileMetadata]: 모든 발견된 파일 메타데이터
        """
        all_files = []
        
        for crawler in self.crawlers:
            logger.info(f"Crawling {crawler.config.name}...")
            try:
                for file_metadata in crawler.crawl(recursive=recursive):
                    all_files.append(file_metadata)
            except Exception as e:
                logger.error(f"Error crawling {crawler.config.name}: {str(e)}")
        
        logger.info(f"Crawl completed: {len(all_files)} files found")
        return all_files
