@echo off
setlocal

:: ==============================================================================
:: Schedules run_daily_update.bat to run automatically every morning at 06:00 AM
:: using Windows Task Scheduler.
:: ==============================================================================

title Setup Live TV Daily Scheduler

cd /d "%~dp0"
set "BAT_PATH=%~dp0run_daily_update.bat"

echo ===============================================================================
echo   SETUP WINDOWS DAILY AUTOMATIC TASK SCHEDULER
echo ===============================================================================
echo.
echo Target Batch File: "%BAT_PATH%"
echo Scheduled Time:    Daily at 06:00 AM (runs silently in background)
echo.

schtasks /create /tn "LiveTV_Daily_Sync" /tr "\"%BAT_PATH%\"" /sc daily /st 06:00 /f

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Windows Task "LiveTV_Daily_Sync" was created successfully!
    echo It will now run every day at 06:00 AM automatically.
    echo To run it manually at any time, just double click run_daily_update.bat.
) else (
    echo.
    echo [NOTE] If this failed, please right-click this file and choose "Run as administrator".
)

echo.
pause
