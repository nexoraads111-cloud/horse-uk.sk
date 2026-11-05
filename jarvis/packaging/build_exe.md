# Збірка Windows .exe (PyInstaller)

## Передумови

- Windows 10/11
- Пройдений `setup.bat`
- Активоване `.venv`

## Команди

```bat
cd jarvis
call .venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconfirm --clean ^
  --name JarvisAssistant ^
  --windowed ^
  --icon assets\icons\jarvis.ico ^
  --add-data "config\defaults.json;config" ^
  --hidden-import PySide6.QtSvg ^
  main.py
```

Результат: `dist\JarvisAssistant\JarvisAssistant.exe`

## Примітки

- `faster-whisper` і моделі Whisper завантажуються в кеш користувача при першому запуску — їх краще не пакувати в exe.
- Piper TTS — окремий бінарник + `.onnx` у `%LOCALAPPDATA%\JarvisAssistant\voices\`.
- Ollama завжди окремий сервіс (`ollama serve`).
- Для відлагодження використовуйте `--console` замість `--windowed`.

## Альтернатива

Залишайтеся на `start.bat` + venv — це найнадійніший спосіб оновлень і діагностики.
