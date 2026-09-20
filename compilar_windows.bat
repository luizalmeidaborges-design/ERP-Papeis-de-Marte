@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_CMD="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo Python 3.10 ou mais recente nao encontrado.
  echo Instale o Python no Windows e marque "Add Python to PATH".
  echo Depois feche e abra novamente o VS Code e execute este arquivo.
  pause
  exit /b 1
)
echo Usando %PYTHON_CMD% para preparar o ambiente.
if not exist .venv\Scripts\python.exe %PYTHON_CMD% -m venv .venv
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name "ERP_Papeis_de_Marte" --icon "assets\marte.ico" --add-data "assets\logo.png;assets" --add-data "assets\marte.ico;assets" --add-data "assets\update_config.json;assets" --collect-all openpyxl --collect-all reportlab app.py
if errorlevel 1 goto failed
echo.
echo Compilacao concluida: dist\ERP_Papeis_de_Marte.exe
pause
exit /b 0
:failed
echo Nao foi possivel compilar. Leia o erro mostrado acima.
pause
exit /b 1
