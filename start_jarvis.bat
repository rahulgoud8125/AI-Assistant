@echo off
cd /d %~dp0
call venv310\Scripts\activate
python jar.py
pause
