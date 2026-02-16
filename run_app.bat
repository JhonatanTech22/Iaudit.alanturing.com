@echo off
echo ========================================================
echo   INICIANDO IAUDIT - SISTEMA DE AUDITORIA
echo ========================================================
echo.
echo [1/3] Parando processos antigos...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1
echo Concluido.

echo.
echo [2/3] Iniciando API Backend (Porta 8000)...
start /B "IAudit Backend" python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
timeout /t 5 >nul

echo.
echo [3/3] Iniciando Frontend (Porta 80)...
echo O site estara disponivel em: http://iaudit.allanturing.com
streamlit run frontend/App.py --server.port 80 --server.address 0.0.0.0

pause
