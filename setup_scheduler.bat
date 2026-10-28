@echo off
title Register Daily Automated Live TV Refresh Task
cd /d "%~dp0"
echo =====================================================================
echo  Registering Daily IPTV Auto-Refresh in Windows Task Scheduler
echo  This will run the checker every morning at 08:00 AM automatically.
echo =====================================================================
echo.

schtasks /create /tn "LiveTV_Playlist_Daily_Refresh" /tr "\"%~dp0run_checker.bat\"" /sc daily /st 08:00 /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Windows Task "LiveTV_Playlist_Daily_Refresh" registered successfully!
    echo It will execute automatically every day at 08:00 AM.
) else (
    echo.
    echo [NOTE] If administrator permissions are required, please right-click this .bat
    echo and select "Run as Administrator".
)
echo.
pause
