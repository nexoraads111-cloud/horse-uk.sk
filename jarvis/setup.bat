@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================
echo   JARVIS — встановлення залежностей
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ПОМИЛКА] Python не знайдено у PATH.
  echo Встановіть Python 3.12+ з https://www.python.org/downloads/
  echo Під час установки поставте галочку "Add Python to PATH".
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)"
if errorlevel 1 (
  echo [ПОМИЛКА] Потрібен Python 3.12 або новіший.
  python --version
  pause
  exit /b 1
)

echo Створюю віртуальне середовище .venv ...
if not exist ".venv" (
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo --------------------------------------------
echo Перевірка Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
  echo [УВАГА] Ollama не в PATH. Завантажте з https://ollama.com
) else (
  echo Ollama знайдено.
  echo Рекомендовані моделі:
  echo   ollama pull llama3.2
  echo   ollama pull llava
)

echo.
echo Голосові моделі Piper ^(опційно^):
echo   1. Встановіть piper: https://github.com/rhasspy/piper/releases
echo   2. Завантажте український голос ^(*.onnx + *.onnx.json^)
echo   3. Покладіть у %%LOCALAPPDATA%%\JarvisAssistant\voices\
echo.
echo Готово. Запустіть start.bat
pause
endlocal
