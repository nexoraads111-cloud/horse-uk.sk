@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

REM Debug build with console window (shows Python tracebacks).
echo Збірка DEBUG-версії з консоллю...

if not exist ".venv\Scripts\python.exe" (
  call setup.bat
  if errorlevel 1 exit /b 1
)
call ".venv\Scripts\activate.bat"
pip install -r requirements.txt
pip install "pyinstaller>=6.3"

if not exist "assets\icons\jarvis.ico" python packaging\make_icon.py

pyinstaller --noconfirm --clean ^
  --name JarvisAssistantConsole ^
  --console ^
  --paths . ^
  --add-data "config\defaults.json;config" ^
  --hidden-import PySide6.QtCore ^
  --hidden-import PySide6.QtGui ^
  --hidden-import PySide6.QtWidgets ^
  --collect-all PySide6 ^
  --collect-all faster_whisper ^
  main.py

echo.
echo Результат: dist\JarvisAssistantConsole\
pause
endlocal
