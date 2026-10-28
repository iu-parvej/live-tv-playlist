@echo off
title BDIX & Live TV Stream Fusion & Optimizer
cd /d "%~dp0"
echo =====================================================================
echo  Starting Daily BDIX & Live TV Refresh...
echo =====================================================================
python main.py
echo.
echo Refresh cycle complete!
pause
