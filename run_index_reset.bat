@echo off
cd /d "%~dp0"
echo [경고] 기존 인덱스를 초기화하고 전체 재인덱싱합니다.
set /p confirm=계속하시겠습니까? (y/n):
if /i not "%confirm%"=="y" (
    echo 취소되었습니다.
    pause
    exit /b
)
echo NAS 전체 재인덱싱 시작 중...
call venv\Scripts\activate
python run_crawl_index.py --reset
pause
