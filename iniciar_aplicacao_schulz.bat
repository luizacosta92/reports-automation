@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Reports Automation - Schulz S.A.

echo ==================================================
echo   Reports Automation - Schulz S.A.
echo   Iniciando a aplicacao...
echo ==================================================
echo.

rem ---------- 1) Checagem do Python 3.10+ ----------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY goto no_python
echo [1/4] Python 3.10+ encontrado: %PY%

rem ---------- 2) Ambiente virtual (venv) ----------
if not exist ".venv\Scripts\python.exe" (
    echo [2/4] Criando o ambiente virtual .venv ...
    %PY% -m venv .venv
    if errorlevel 1 goto venv_fail
) else (
    echo [2/4] Ambiente virtual .venv ja existe.
)
call ".venv\Scripts\activate.bat"

rem ---------- 3) Instalacao das bibliotecas ----------
echo [3/4] Instalando as bibliotecas do requirements.txt ...
python -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto pip_fail

rem ---------- Interface web (pasta web\ ja vem compilada no repositorio) ----------
if not exist "web\index.html" (
    where npm >nul 2>&1
    if errorlevel 1 goto no_web
    echo Compilando a interface web com o npm ...
    pushd frontend-calibra
    call npm ci
    call npm run build -- --outDir ../web --emptyOutDir
    popd
)
if not exist "web\index.html" goto no_web

rem ---------- 4) Inicializacao da API e abertura do navegador ----------
echo [4/4] Iniciando a API em http://127.0.0.1:8000 ...
start "Reports Automation - API (feche esta janela para encerrar)" /d "%CD%" cmd /k .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

set /a TRIES=0
:wait_api
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto api_ready
set /a TRIES+=1
if %TRIES% GEQ 30 goto api_fail
timeout /t 1 /nobreak >nul
goto wait_api

:api_ready
echo.
echo Aplicacao no ar. Abrindo o navegador...
start "" "http://127.0.0.1:8000"
echo.
echo Para encerrar, feche a janela "Reports Automation - API".
echo.
pause
exit /b 0

:no_python
echo [ERRO] Python 3.10 ou superior nao foi encontrado no PATH.
echo Instale em https://www.python.org/downloads/ e marque a opcao "Add python.exe to PATH".
echo Depois execute este arquivo novamente.
pause
exit /b 1

:venv_fail
echo [ERRO] Nao foi possivel criar o ambiente virtual.
pause
exit /b 1

:pip_fail
echo [ERRO] Falha ao instalar as bibliotecas. Verifique a conexao com a internet.
pause
exit /b 1

:no_web
echo [ERRO] A interface web (pasta web) nao foi encontrada e o npm nao esta instalado.
echo Instale o Node.js (https://nodejs.org) ou restaure a pasta web do repositorio.
pause
exit /b 1

:api_fail
echo [ERRO] A API nao respondeu em 30 segundos. Veja a janela "Reports Automation - API".
pause
exit /b 1
