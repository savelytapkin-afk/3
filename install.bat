@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
set "PYTHON_BIN=python"
set "VENV_DIR=.venv"

where %PYTHON_BIN% >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found in PATH
  exit /b 1
)

%PYTHON_BIN% -m venv %VENV_DIR%
if errorlevel 1 exit /b 1

call %VENV_DIR%\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1

call %VENV_DIR%\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

if not exist profiles.txt if exist profiles.txt.example (
  copy /Y profiles.txt.example profiles.txt >nul
)

echo [OK] Installation complete
echo Activate env: %VENV_DIR%\Scripts\activate
echo Run app: python app.py
endlocal
