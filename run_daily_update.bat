@echo off
setlocal enabledelayedexpansion

:: ==============================================================================
:: Live TV Playlist Auto Daily Sync & Self-Healing Pipeline
:: Scans Curated VIP channels, checks all playlist sources, fixes broken links,
:: normalizes categories (Televizo / IPTV Pro ready), and auto-pushes to GitHub.
:: ==============================================================================

title Live TV Playlist - Auto Daily Sync

:: Change working directory to this script's directory
cd /d "%~dp0"

echo ===============================================================================
echo   LIVE TV PLAYLIST - AUTO DAILY SYNC ^& SELF-HEALING PIPELINE
echo   Time: %date% %time%
echo ===============================================================================
echo.

:: Check for Python installation
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.10+ from python.org and add it to your PATH.
    echo.
    pause
    exit /b 1
)

:: Run the Python daily sync pipeline
echo [INFO] Running daily sync pipeline...
python auto_daily_sync.py %*

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Daily sync completed with warnings or encountered an error.
    echo Please check the log messages above.
) else (
    echo.
    echo [SUCCESS] Daily sync completed and playlists pushed to GitHub!
)

echo.
echo ===============================================================================
echo Closing in 10 seconds (or press any key to exit immediately)...
echo ===============================================================================
timeout /t 10
exit /b %errorlevel%
