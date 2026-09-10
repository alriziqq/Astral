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

where docker >nul 2>&1
if errorlevel 1 goto docker_unavailable

echo Starting Docker Desktop...
docker desktop start >nul 2>&1

echo Waiting for Docker engine...
set /a docker_attempts=0
:wait_for_docker
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready
set /a docker_attempts+=1
if %docker_attempts% GEQ 30 goto docker_unavailable
timeout /t 2 /nobreak >nul
goto wait_for_docker

:docker_ready
echo Starting SearXNG...
docker start searxng >nul 2>&1
if errorlevel 1 echo Warning: SearXNG container could not be started.
goto dependencies

:docker_unavailable
echo Warning: Docker engine is not ready. Astral will start without SearXNG.

:dependencies

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
