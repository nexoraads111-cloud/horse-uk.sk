@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================
echo   JARVIS — збірка Windows .exe (PyInstaller)
echo ============================================
echo.
echo Ollama, Piper і моделі Whisper НЕ пакуються в exe.
echo Їх потрібно встановити окремо на ПК користувача.
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ПОМИЛКА] Python не знайдено в PATH.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Віртуальне середовище відсутнє — запускаю setup.bat ...
  call setup.bat
  if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
pip install "pyinstaller>=6.3"

echo.
echo Перевірка імпортів перед збіркою...
python packaging\verify_packaging.py
if errorlevel 1 (
  echo [ПОМИЛКА] verify_packaging.py не пройшов.
  pause
  exit /b 1
)

if not exist "assets\icons\jarvis.ico" (
  echo Генерую просту іконку assets\icons\jarvis.ico ...
  python packaging\make_icon.py
)

set OUTDIR=dist\JarvisAssistant
echo.
echo Запуск PyInstaller ^(onedir^)...
pyinstaller --noconfirm --clean JarvisAssistant.spec
if errorlevel 1 (
  echo.
  echo [ПОМИЛКА] PyInstaller завершився з помилкою.
  pause
  exit /b 1
)

if not exist "%OUTDIR%\JarvisAssistant.exe" (
  echo [ПОМИЛКА] Не знайдено %OUTDIR%\JarvisAssistant.exe
  pause
  exit /b 1
)

copy /Y "README.md" "%OUTDIR%\README-JARVIS.md" >nul
copy /Y "packaging\DIST_README_uk.txt" "%OUTDIR%\ЯК_ЗАПУСТИТИ.txt" >nul 2>nul
if not exist "%OUTDIR%\ЯК_ЗАПУСТИТИ.txt" (
  copy /Y "packaging\DIST_README_uk.txt" "%OUTDIR%\HOW_TO_RUN.txt" >nul
)

echo.
echo ============================================
echo   ГОТОВО
echo ============================================
echo exe:  %CD%\%OUTDIR%\JarvisAssistant.exe
echo тека: %CD%\%OUTDIR%\
echo.
echo Перед запуском exe переконайтесь:
echo   1^) Ollama встановлена і запущена
echo   2^) ollama pull llama3.2
echo   3^) ^(опційно^) Piper + uk голос у %%LOCALAPPDATA%%\JarvisAssistant\voices\
echo.
echo Для відлагодження з консоллю:
echo   set JARVIS_CONSOLE=1 ^& build_exe_console.bat
echo.
pause
endlocal
