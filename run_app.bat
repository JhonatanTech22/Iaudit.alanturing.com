@echo off
setlocal
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
echo Uma nova janela sera aberta para o backend. NAO A FECHE.
start "IAudit Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 5 >nul

echo.
echo [3/3] Iniciando Frontend (Porta 8501)...
echo O site estara disponivel em: http://localhost:8501
set BACKEND_URL=http://localhost:8000
start "IAudit Frontend" cmd /k "streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"

echo.
echo SISTEMA INICIADO.
echo Se as janelas fecharem imediatamente, houve um erro.
echo Verifique as mensagens de erro nas janelas abertas.
pause
