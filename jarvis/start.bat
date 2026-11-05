@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Віртуальне середовище не знайдено. Спочатку запустіть setup.bat
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Запуск JARVIS...
python main.py
if errorlevel 1 (
  echo.
  echo JARVIS завершився з помилкою. Див. логи у %%LOCALAPPDATA%%\JarvisAssistant\logs\
  pause
)
endlocal
