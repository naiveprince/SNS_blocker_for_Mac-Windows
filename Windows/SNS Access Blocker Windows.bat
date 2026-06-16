@echo off
setlocal
cd /d "%~dp0"

where pyw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pyw.exe -3 "%CD%\app.py"
  exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pythonw.exe "%CD%\app.py"
  exit /b 0
)

where py.exe >nul 2>nul
if not errorlevel 1 (
  py -3 "%CD%\app.py"
  pause
  exit /b %ERRORLEVEL%
)

python "%CD%\app.py"
pause
