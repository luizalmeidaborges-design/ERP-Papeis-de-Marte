@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (
  echo Instale o Git for Windows antes de executar este arquivo.
  exit /b 1
)
where gh >nul 2>nul
if errorlevel 1 (
  echo Instale o GitHub CLI e execute gh auth login antes de continuar.
  exit /b 1
)
gh auth status >nul 2>nul
if errorlevel 1 (
  echo Execute gh auth login para conectar a sua conta.
  exit /b 1
)
gh repo view "luizalmeidaborges-design/ERP-Papeis-de-Marte" >nul 2>nul
if not errorlevel 1 (
  echo O repositorio ja existe. Confira antes de enviar arquivos por cima.
  exit /b 1
)
if not exist .git (
  git init -b main
  if errorlevel 1 goto failed
)
git add -A
if errorlevel 1 goto failed
git ls-files --error-unmatch "assets/Precificação.xlsx" >nul 2>nul
if not errorlevel 1 (
  echo A planilha privada foi selecionada. Publicacao cancelada.
  exit /b 1
)
git -c user.name="Papeis de Marte" -c user.email="noreply@papeisdemarte.local" commit -m "Versao inicial do ERP com atualizacao automatica"
if errorlevel 1 goto failed
gh repo create "luizalmeidaborges-design/ERP-Papeis-de-Marte" --public --source=. --remote=origin --push
if errorlevel 1 goto failed
echo Repositorio criado. Abra Actions no GitHub para publicar a versao 1.1.0.
exit /b 0
:failed
echo Nao foi possivel criar o repositorio. Confira o erro mostrado acima.
exit /b 1
