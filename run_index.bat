@echo off
cd /d "%~dp0"
echo NAS 인덱싱 시작 중...
call venv\Scripts\activate
python run_crawl_index.py
pause
