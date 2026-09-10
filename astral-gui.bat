@echo off
setlocal
title Astral GUI
chcp 65001 >nul

cd /d "%~dp0"
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"

echo Starting Astral GUI...
echo.

where node >nul 2>&1
if errorlevel 1 goto missing_node

where npx.cmd >nul 2>&1
if errorlevel 1 goto missing_node

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm.cmd install
    if errorlevel 1 goto failed
    cd ..
)

call npx.cmd -y @tauri-apps/cli dev
if errorlevel 1 goto failed
goto done

:missing_node
echo Node.js is not installed or is not available in PATH.
echo Install Node.js LTS, then run this file again.
goto failed

:failed
echo.
echo Astral GUI could not be started.
pause
exit /b 1

:done
endlocal
