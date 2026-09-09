@echo off
title Astral
chcp 65001 >nul
set PYTHONUTF8=1

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
goto start_astral

:docker_unavailable
echo Warning: Docker engine is not ready. Astral will start without SearXNG.

:start_astral

echo Starting Astral...
python "%~dp0Astral.py"

pause
