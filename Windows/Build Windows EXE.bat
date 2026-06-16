@echo off
setlocal
cd /d "%~dp0"

where py.exe >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3"
) else (
  set "PY=python"
)

%PY% -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
  %PY% -m pip install --user pyinstaller
  if errorlevel 1 goto failed
)

%PY% -m PyInstaller --noconfirm --clean --windowed --onefile --name "SNS Access Blocker" app.py
if errorlevel 1 goto failed

echo.
echo Built: dist\SNS Access Blocker.exe
pause
exit /b 0

:failed
echo.
echo Build failed.
pause
exit /b 1
