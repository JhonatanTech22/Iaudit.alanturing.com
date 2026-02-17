echo ========================================================
echo   ENVIANDO CODIGO PARA O GITHUB
echo ========================================================
cd /d "%~dp0"
echo.
echo O Git vai pedir suas credenciais (Login/Senha ou Token).
echo Se abrir uma janela do navegador, faca o login nela.
echo.
git push -u origin main
echo.
if %errorlevel% neq 0 (
    echo [ERRO] Nao foi possivel enviar. Verifique seu login.
) else (
    echo [SUCESSO] Codigo enviado para o GitHub!
)
pause
