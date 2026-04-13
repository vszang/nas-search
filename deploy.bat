@echo off
REM 배포 자동화 스크립트 (Windows)
REM 사용: deploy.bat

setlocal enabledelayedexpansion

REM 색상 및 로그 함수
set GREEN=
set YELLOW=
set RED=
set NC=

REM 프로젝트 루트 확인
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt를 찾을 수 없습니다.
    echo 프로젝트 루트 디렉토리에서 실행하세요.
    exit /b 1
)

echo [INFO] 배포 스크립트 시작...
echo.

REM 1. 환경 설정 확인
echo [INFO] 1. 환경 설정 확인...
if not exist ".env" (
    if exist ".env.example" (
        echo [WARN] .env 파일이 없습니다. .env.example을 복사합니다.
        copy .env.example .env
        echo [WARN] .env 파일을 실제 값으로 수정하세요!
    ) else (
        echo [ERROR] .env 또는 .env.example 파일이 없습니다.
        exit /b 1
    )
) else (
    echo [INFO] .env 파일 확인됨
)

REM 2. 가상환경 생성/활성화
echo [INFO] 2. Python 가상환경 확인...
if not exist "venv" (
    echo [INFO] 가상환경 생성 중...
    python -m venv venv
) else (
    echo [INFO] 기존 가상환경 사용
)

call venv\Scripts\activate.bat
echo [INFO] 가상환경 활성화됨

REM 3. Python 버전 확인
echo [INFO] 3. Python 버전 확인...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python 버전: !PYTHON_VERSION!

REM 4. 의존성 설치
echo [INFO] 4. 의존성 설치 중...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
echo [INFO] 의존성 설치 완료

REM 5. 테스트 실행 (pytest 확인)
echo [INFO] 5. 테스트 실행 중...
where pytest >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    pytest tests -q --tb=short
    if %ERRORLEVEL% NEQ 0 (
        echo [WARN] 일부 테스트가 실패했습니다.
    )
) else (
    echo [WARN] pytest가 설치되지 않았습니다. 테스트 건너뜀.
)

REM 6. Node.js/npm 확인
echo [INFO] 6. Node.js 환경 확인...
where npm >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
    echo [INFO] npm 버전: !NPM_VERSION!
    echo [INFO] frontend 의존성 설치 중...
    cd frontend
    call npm install -q
    cd ..
    echo [INFO] frontend 의존성 설치 완료
) else (
    echo [WARN] npm이 설치되지 않았습니다. 프론트엔드를 수동으로 구성하세요.
)

REM 7. 디렉토리 생성
echo [INFO] 7. 필요한 디렉토리 생성...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "data\cache" mkdir data\cache
echo [INFO] 디렉토리 생성 완료

REM 8. 요약 정보 출력
echo.
echo [INFO] 8. 배포 준비 완료!
echo.
echo 📋 배포 정보:
echo ═══════════════════════════════════════
echo 프로젝트: 사내 NAS 검색 MCP
echo Python: !PYTHON_VERSION!

where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('node --version') do echo Node.js: %%i
) else (
    echo Node.js: 설치 필요
)

echo.
echo 🚀 서버 시작 방법:
echo ═══════════════════════════════════════
echo 1. Flask 백엔드 (현재 터미널):
echo    venv\Scripts\activate.bat
echo    python app.py
echo.
echo 2. Vite 프론트엔드 (새 터미널):
echo    cd frontend
echo    npm run dev
echo.
echo 3. 크롤러 (선택사항, 새 터미널):
echo    venv\Scripts\activate.bat
echo    python -m src.crawler
echo.
echo ✅ 배포 준비 완료!
echo ═══════════════════════════════════════
echo.

REM 가상환경 유지
endlocal
