@echo off
title Live TV Web Dashboard
cd /d "%~dp0"
echo Starting Live TV Pro Web Dashboard at http://localhost:8080 ...
start http://localhost:8080
python main.py --web
pause
