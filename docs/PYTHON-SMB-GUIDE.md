# Python SMB/CIFS 프로토콜 학습 가이드

이 문서는 사내 NAS 검색 MCP 개발 중 사용할 SMB 프로토콜과 Python 라이브러리에 대한 학습 자료입니다.

## 1. SMB/CIFS 프로토콜이란?

### 개요
**SMB** (Server Message Block)는 네트워크를 통해 파일, 프린터, 기타 리소스를 공유하는 프로토콜입니다.

- **CIFS** (Common Internet File System): SMB의 공개 버전 (SMB 1.0 기반)
- **모던 SMB**: SMB 2.0+는 Windows Vista 이후 표준

### SMB 버전별 특징

| 버전 | 도입 | 주요 특징 | 보안 |
|------|------|---------|------|
| **SMB 1.0** | 1983-1990년대 | 레거시, 매우 느림 | ❌ 취약함 (WannaCry) |
| **SMB 2.0** | Windows Vista | 성능 2배 향상 | ⚠️ 보통 |
| **SMB 2.1** | Windows 7 | 대용량 파일 지원 | ⚠️ 보통 |
| **SMB 3.0** | Windows 8 | 암호화, 멀티채널 | ✅ 강함 |
| **SMB 3.1.1** | Windows 10+ | 모던 암호화 | ✅ 강함 |

### SMB 아키텍처 (계층)

```
┌─────────────────────────────────┐
│   응용 프로그램                  │  (클라이언트 ex: Explorer)
├─────────────────────────────────┤
│   SMB 프로토콜                   │  (파일/프린터/메시지 공유)
├─────────────────────────────────┤
│   NetBIOS / TCP/IP              │  (전송 계층, 포트 445)
├─────────────────────────────────┤
│   네트워크 카드 (NIC)            │  (물리 계층)
└─────────────────────────────────┘
```

### SMB 통신 흐름

```
1. 연결 설정 (Negotiate)
   클라이언트 → 서버: "SMB 3.0 사용할래?"
   
2. 세션 설정 (Session Setup)
   클라이언트 → 서버: "사용자명/비밀번호로 인증해줘"
   ↓
   서버 → 클라이언트: "OK, 세션 ID 발급!"
   
3. 트리 연결 (Tree Connect)
   클라이언트 → 서버: "\\nas1\share 연결할래?"
   ↓
   서버 → 클라이언트: "OK, 트리 ID 발급!"
   
4. 파일 작업 (File Operations)
   - CREATE: 파일 생성/열기
   - READ: 파일 읽기
   - WRITE: 파일 쓰기
   - DELETE: 파일 삭제
   - QUERY_FILE_INFO: 파일 정보 조회
   
5. 연결 해제
   클라이언트 → 서버: "연결 끝낼게"
```

### 포트 정보

| 서비스 | 포트 | 프로토콜 | 설명 |
|------|------|---------|------|
| **SMB** | **445** | **TCP** | ✅ 모던 방식 (직접 TCP) |
| **NetBIOS** | 139 | TCP/UDP | ❌ 레거시 (SMB over NetBIOS) |
| **Kerberos** | 88 | TCP/UDP | 도메인 인증 |
| **LDAP** | 389 | TCP | 계정/권한 조회 |

## 2. Python SMB 라이브러리 비교

### 주요 라이브러리 3가지

| 라이브러리 | 유지보수 | 성능 | 사용 난이도 | 기능 | 추천 |
|-----------|---------|------|-----------|------|------|
| **smbclient** | ✅ 활발 | ⭐⭐⭐⭐ | 쉬움 | 풍부 | ✅ **추천** |
| **pysmb** (impacket) | ✅ 활발 | ⭐⭐⭐ | 보통 | 풍부 | ⭐ 대안 |
| **smb-pyshare** | ⚠️ 유지보수 중단 | ⭐⭐ | 어려움 | 기본 | ❌ 사용금지 |

### 추천: `smbclient`

```bash
pip install smbclient
```

**장점**
- ✅ 최신 SMB 3.0+ 지원
- ✅ Pythonic API (쉬운 인터페이스)
- ✅ 문서 및 커뮤니티 활발
- ✅ Windows/Linux/Mac 모두 지원
- ✅ asyncio 지원

**설치 및 기본 사용**

```python
import smbclient

# 1. 연결 설정
# Kerberos 인증 (도메인 환경)
smbclient.ClientConfig(auth_try_ntlm=True)

# 2. 파일 나열
with smbclient.SMBFile(
    "//nas1/share",
    username="user@domain",
    password="password"
) as f:
    files = f.listdir()

# 3. 파일 읽기
with smbclient.open_file(
    "//nas1/share/document.txt",
    mode="rb",
    username="user@domain",
    password="password"
) as f:
    content = f.read()
```

### 대안: `pysmb` (impacket)

더 저수준 제어가 필요한 경우 사용하실 수 있습니다:

```bash
pip install impacket
```

```python
from impacket.smbconnection import SMBConnection

# 연결
conn = SMBConnection(
    username="user",
    password="password",
    my_name="client",
    remote_name="nas1",
    domain="",  또는 도메인명
    use_ntlm_v2=True
)
conn.connect("192.168.1.100", port=445)

# 공유 폴더 나열
shares = conn.listShares()

# 파일 나열
files = conn.listPath(share_name, path)

# 연결 해제
conn.close()
```

## 3. MCP 프로젝트에 적용되는 개념

### 3-1. 캐싱 전략 (옵션 2)

```python
# 개념: NAS에서 조회한 파일 목록을 로컬 SQLite에 저장
# 장점: 반복 조회 시 속도 향상
# 문제: 캐시 유효성 - 언제까지 신뢰할 것인가?

class NASCache:
    def __init__(self, db_path="nas_cache.db"):
        # SQLite 초기화
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # 테이블 생성
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE,
                name TEXT,
                size INTEGER,
                modified TIMESTAMP,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def get_cached(self, path, max_age_seconds=3600):
        """
        캐시에서 조회
        - max_age_seconds: 캐시 유효 기간
        - 기간 초과 시 None 반환 (NAS에서 다시 조회하면 됨)
        """
        self.cursor.execute("""
            SELECT * FROM files 
            WHERE path = ? 
            AND datetime(cached_at, '+' || ? || ' seconds') > datetime('now')
        """, (path, max_age_seconds))
        return self.cursor.fetchone()
```

### 3-2. 에러 처리

```python
# SMB 접근 중 발생할 수 있는 에러들

class NASError(Exception):
    """기본 NAS 에러"""
    pass

class ConnectionError(NASError):
    """NAS 연결 실패"""
    # 원인: 네트워크 끊김, 서버 다운, IP 주소 변경
    pass

class AuthenticationError(NASError):
    """인증 실패"""
    # 원인: 잘못된 계정/비밀번호, 권한 부족
    pass

class FileNotFoundError(NASError):
    """파일을 찾을 수 없음"""
    pass

class TimeoutError(NASError):
    """작업 타임아웃"""
    # 원인: 네트워크 느림, 파일 매우 큼, NAS 과부하
    pass
```

### 3-3. 동시성 안전 (Thread Safety)

```python
# SMB 라이브러리는 기본적으로 thread-safe하지 않음
# 여러 요청을 동시에 처리하려면 Lock 필요

import threading
from typing import Dict

class NASManager:
    def __init__(self):
        self.connections: Dict = {}
        self.lock = threading.RLock()  # 재진입 가능한 Lock
    
    def get_connection(self, nas_name: str):
        """
        NAS별 고유 연결을 관리
        - 각 NAS마다 하나의 연결만 유지
        - 동시 요청은 큐에 대기
        """
        with self.lock:
            if nas_name not in self.connections:
                # 새 연결 생성
                self.connections[nas_name] = self._create_connection(nas_name)
            return self.connections[nas_name]
    
    def search_files(self, nas_name: str, query: str):
        """Thread-safe 검색"""
        with self.lock:
            conn = self.get_connection(nas_name)
            # 검색 수행
```

## 4. 알아두면 좋은 네트워킹 개념

### 4-1. NetBIOS 이름 vs IP 주소

```
// 방식 1: IP 주소 + 포트 (권장)
//192.168.1.100:445/share

// 방식 2: NetBIOS 이름 (과거 방식)
//nas1/share

// 방식 3: FQDN (도메인 환경)
//nas1.company.com/share
```

### 4-2. 인증 메커니즘

```
┌─────────────────────────────────────┐
│  인증 방식 선택                      │
├─────────────────────────────────────┤
│  1. 로컬 계정                        │  (간단)
│     username: "user"                │
│     password: "pass"                │
├─────────────────────────────────────┤
│  2. 도메인 계정 (NTLM)              │  (일반적)
│     username: "user@domain"         │
│     password: "pass"                │
│     domain: "company.com"           │
├─────────────────────────────────────┤
│  3. Kerberos (고급)                 │
│     SSO (Single Sign-On)            │
│     자동 인증, 가장 안전             │
└─────────────────────────────────────┘
```

## 5. 성능 최적화 팁

### 5-1. 연결 재사용
```python
# ❌ 나쁜 예: 매번 새 연결
for file in files:
    with SMBConnection(...) as conn:
        conn.get_file_info(file)  # 1000번 연결 설정!

# ✅ 좋은 예: 연결 재사용
with SMBConnection(...) as conn:
    for file in files:
        conn.get_file_info(file)  # 1번만 연결 설정
```

### 5-2. 배치 작업
```python
# ❌ 나쁜 예: 순차 처리
for file in files:
    info = conn.get_file_info(file)
    db.insert(info)

# ✅ 좋은 예: 배치 처리
infos = conn.get_file_info_batch(files)
db.insert_batch(infos)
```

### 5-3. 타임아웃 설정
```python
# 무한 대기 방지
smbclient.ClientConfig(
    tcp_connect_timeout=5,  # 5초
    socket_options=[(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)]
)
```

## 6. 보안 고려사항

### 6-1. 인증정보 저장
```python
# ❌ 나쁜 예: 코드에 하드코딩
username = "user"
password = "pass123"

# ✅ 좋은 예: 환경변수 또는 설정파일
import os
username = os.getenv("NAS_USERNAME")
password = os.getenv("NAS_PASSWORD")

# ✅ 더 나은 예: 시스템 키링
import keyring
password = keyring.get_password("nas", username)
```

### 6-2. SMB 서명 & 암호화
```python
# 지원되는 경우 반드시 활성화
smbclient.ClientConfig(
    signing_required=True,      # SMB 서명 필수
    use_ssl=True,              # SSL/TLS 사용 (가능한 경우)
    require_encryption=True    # 암호화 필수
)
```

## 7. 참고 자료

- [smbclient 공식 문서](https://smbclient.readthedocs.io/)
- [impacket 문서](https://impacket.readthedocs.io/)
- [Microsoft SMB 명세](https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-smb/)
- [Synology SMB 가이드](https://www.synology.com/)

## 8. 다음 학습 단계

1. ✅ 이론 학습 (현재 이 문서)
2. [ ] 실습 1: SMB 연결 테스트 (Python 코드)
3. [ ] 실습 2: 파일 나열 및 검색 구현
4. [ ] 실습 3: 캐싱 레이어 구현
5. [ ] 실습 4: MCP 인터페이스 구현
