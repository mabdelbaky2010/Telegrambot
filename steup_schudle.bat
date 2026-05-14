@echo off
:: ============================================================
::  TradingView Screener  —  Windows Task Scheduler Setup
::  Runs tv_screener.py every 3 minutes, starting now.
::  Run this file as Administrator (right-click > Run as admin)
:: ============================================================

echo.
echo  ============================================
echo   TradingView EMA Screener — Setup
echo  ============================================
echo.

:: ── Step 1: Check Python ────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python from https://python.org
    echo          Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo  Python found: %%i

:: ── Step 2: Install requests ─────────────────────────────────
echo.
echo  Installing required packages...
python -m pip install requests --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] pip install failed. Try running: python -m pip install requests
    pause
    exit /b 1
)
echo  [OK] requests installed.

:: ── Step 3: Locate the script ────────────────────────────────
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%tv_screener.py

if not exist "%SCRIPT_PATH%" (
    echo  [ERROR] tv_screener.py not found at:
    echo          %SCRIPT_PATH%
    echo          Make sure both files are in the same folder.
    pause
    exit /b 1
)
echo  [OK] Script found: %SCRIPT_PATH%

:: ── Step 4: Create the scheduled task ───────────────────────
echo.
echo  Creating Windows Scheduled Task...

:: Delete old task if it exists
schtasks /delete /tn "TVEMAScreener" /f >nul 2>&1

:: Create task that triggers every 3 minutes, indefinitely
schtasks /create ^
  /tn "TVEMAScreener" ^
  /tr "python \"%SCRIPT_PATH%\"" ^
  /sc MINUTE ^
  /mo 3 ^
  /st 00:00 ^
  /du 9999:59 ^
  /ri 3 ^
  /f ^
  /rl HIGHEST

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to create scheduled task.
    echo          Please right-click this file and choose "Run as administrator".
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   SUCCESS! Task "TVEMAScreener" is active.
echo   It will run tv_screener.py every 3 min.
echo.
echo   To stop it:   schtasks /delete /tn "TVEMAScreener" /f
echo   To run now:   schtasks /run /tn "TVEMAScreener"
echo   View logs:    screener_log.txt  (same folder)
echo  ============================================
echo.
pause
