@echo off
cd /d "%~dp0"
echo NAS Search Flask 서버 시작 중...
call venv\Scripts\activate
python app.py
pause
