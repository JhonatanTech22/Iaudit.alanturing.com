@echo off
setlocal
echo ========================================================
echo   CONFIGURACAO DE ACESSO EXTERNO (NGROK)
echo ========================================================
echo.
echo Para liberar o acesso, voce precisa de um TOKEN GRATIS.
echo.
echo 1. Acesse: https://dashboard.ngrok.com/get-started/your-authtoken
echo 2. Faca login (com Google ou GitHub).
echo 3. Copie o codigo que comeca com "2..."
echo.
set /p NGROK_TOKEN="Cole seu Authtoken aqui e aperte ENTER: "

if not exist "C:\Users\Micro\.ngrok2\ngrok.yml" (
    if "%NGROK_TOKEN%"=="" (
         echo Voce nao colou o token!
         echo Se ja configurou antes, apenas aperte ENTER vazios para continuar tentar sem token.
    )
)

if not "%NGROK_TOKEN%"=="" (
    echo Configurando Ngrok...
    ngrok config add-authtoken %NGROK_TOKEN%
)

echo.
echo ========================================================
echo   INICIANDO TUNEL...
echo   O site estara disponivel no link "Forwarding" abaixo.
echo   Exemplo: https://xy12-34.ngrok-free.app
echo ========================================================
echo.
ngrok http 81
pause
