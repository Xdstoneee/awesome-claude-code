@echo off
REM PALANTIR — one-shot setup for Windows (native, no WSL)
REM Requires Python 3.10+ from python.org

echo.
echo   PALANTIR // GLOBAL SITUATIONAL AWARENESS // SETUP
echo.

SET REPO_DIR=%~dp0..
SET VENV_DIR=%REPO_DIR%\venv

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo   ERROR: Python not found. Download from https://python.org
    pause & exit /b 1
)

FOR /F "tokens=2" %%V IN ('python --version 2^>^&1') DO SET PY_VER=%%V
echo   [1/3] Python %PY_VER% found

REM Create venv
IF NOT EXIST "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    echo   [2/3] Created venv
) ELSE (
    echo   [2/3] venv already exists
)

REM Install packages
echo   [3/3] Installing packages...
"%VENV_DIR%\Scripts\pip" install --upgrade pip --quiet
"%VENV_DIR%\Scripts\pip" install -r "%REPO_DIR%\palantir\requirements.txt"

REM .env
IF NOT EXIST "%REPO_DIR%\.env" (
    copy "%REPO_DIR%\.env.example" "%REPO_DIR%\.env" >nul
    echo   Created .env — add your API keys there
)

REM Verify
echo.
echo   Verifying...
"%VENV_DIR%\Scripts\python" -c "from PyQt6.QtWidgets import QApplication; print('  PyQt6 OK')"
IF ERRORLEVEL 1 (
    echo   ERROR: PyQt6 import failed. Run: pip install PyQt6 PyQt6-WebEngine
    pause & exit /b 1
)

echo.
echo   Setup complete! Run with:
echo     venv\Scripts\python -m palantir
echo.
pause
