@echo off
setlocal
cd /d "%~dp0"
if not exist .git (
  echo Abra a pasta criada por criar_repositorio_windows.bat antes de enviar alteracoes.
  exit /b 1
)
git add -A
if errorlevel 1 goto failed
git ls-files --error-unmatch "assets/Precificação.xlsx" >nul 2>nul
if not errorlevel 1 (
  echo A planilha privada foi selecionada. Publicacao cancelada.
  exit /b 1
)
git diff --cached --quiet
if not errorlevel 1 (
  echo Nao ha alteracoes para enviar.
  exit /b 0
)
git -c user.name="Papeis de Marte" -c user.email="noreply@papeisdemarte.local" commit -m "Atualizacao do ERP"
if errorlevel 1 goto failed
git push
if errorlevel 1 goto failed
echo Codigo enviado. No GitHub, abra Actions e publique a proxima versao.
exit /b 0
:failed
echo Nao foi possivel enviar as alteracoes. Confira o erro acima.
exit /b 1
