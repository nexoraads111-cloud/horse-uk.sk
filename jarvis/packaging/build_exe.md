# Збірка Windows `.exe` (PyInstaller)

## Одна команда (рекомендовано)

На **Windows 10/11**, у теці `jarvis`:

```bat
build_exe.bat
```

Скрипт:
1. створить/використає `.venv` і встановить залежності + PyInstaller;
2. прогонить `packaging\verify_packaging.py`;
3. збереже onedir-збірку в `dist\JarvisAssistant\JarvisAssistant.exe`.

Debug-збірка з консоллю (traceback):

```bat
build_exe_console.bat
```

## Передумови

| Компонент | У .exe? | Примітка |
|-----------|---------|----------|
| Python 3.12+ | ні (лише для збірки) | Потрібен на машині, де збираєте |
| PySide6 / код JARVIS | **так** | Пакується PyInstaller |
| **Ollama** | **ні** | Окремий інсталятор: https://ollama.com |
| Моделі LLM (`llama3.2`, `llava`) | **ні** | `ollama pull …` |
| Whisper weights | **ні** | Качаються в кеш при першому STT |
| Piper + uk `.onnx` | **ні** | `%LOCALAPPDATA%\JarvisAssistant\voices\` |

Пакувати Ollama всередину exe **непрактично** (окремий runtime, GPU/CPU backends, моделі гігабайти). Залишайте Ollama зовнішньою службою.

## Файли пакування

| Файл | Роль |
|------|------|
| `build_exe.bat` | Збірка для користувача |
| `build_exe_console.bat` | Debug exe з консоллю |
| `JarvisAssistant.spec` | Конфіг PyInstaller (hiddenimports, datas, onedir) |
| `packaging/verify_packaging.py` | Перевірка до збірки (працює і на Linux) |
| `packaging/make_icon.py` | Генерація `assets/icons/jarvis.ico` |
| `packaging/DIST_README_uk.txt` | Текст «як запустити» у `dist\` |

## Результат

```
jarvis\dist\JarvisAssistant\
  JarvisAssistant.exe
  _internal\          (DLL, Qt, Python libs)
  ЯК_ЗАПУСТИТИ.txt / HOW_TO_RUN.txt
  README-JARVIS.md
```

Розповсюджуйте **всю теку** `JarvisAssistant`, не лише один `.exe`.

## Linux / CI

Повноцінний Windows `.exe` на Linux **не збирається**. Можна перевірити конфіг:

```bash
cd jarvis
python3 packaging/verify_packaging.py
PYINSTALLER_SMOKE=1 python3 packaging/verify_packaging.py   # опційно Analysis
```

## Типові проблеми

- Антивірус ріже PyInstaller — додайте виняток на `dist\`.
- Відсутня Ollama → JARVIS стартує, але чат покаже помилку підключення.
- Великий розмір `_internal` — нормально через Qt + ctranslate2.
