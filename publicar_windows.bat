@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto usage
if "%~2"=="" goto usage
where gh >nul 2>nul
if errorlevel 1 (
  echo Instale o GitHub CLI e execute gh auth login antes de publicar.
  exit /b 1
)
gh auth status >nul 2>nul
if errorlevel 1 (
  echo Entre na sua conta usando gh auth login.
  exit /b 1
)
set "PYTHON_CMD=py -3"
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul
if errorlevel 1 set "PYTHON_CMD=python"
%PYTHON_CMD% configurar_release.py "%~1" "%~2"
if errorlevel 1 goto failed
call compilar_windows.bat
if errorlevel 1 goto failed
.venv\Scripts\python.exe gerar_manifesto.py --repo "%~1"
if errorlevel 1 goto failed
gh release create "v%~2" "dist\ERP_Papeis_de_Marte.exe" "dist\update.json" --repo "%~1" --title "Papéis de Marte v%~2" --notes "Atualização do ERP Papéis de Marte." --latest
if errorlevel 1 goto failed
echo Publicacao concluida. A cliente recebera a versao quando abrir o ERP com internet.
exit /b 0
:usage
echo Uso: publicar_windows.bat USUARIO/REPOSITORIO 1.2.0
exit /b 1
:failed
echo Falha ao preparar ou publicar. Confira o erro acima.
exit /b 1
