# JARVIS — локальний український AI-асистент (Windows)

Голосовий і текстовий асистент для Windows: **Ollama** (локальна LLM + vision), **faster-whisper** (розпізнавання української мови), **Piper** (офлайн TTS), безпечне керування програмами, знімки екрана, інтеграція з **Cursor IDE**. Без платних API.

## Швидкий старт (без редагування Python)

1. Встановіть [Python 3.12+](https://www.python.org/downloads/) (**Add to PATH**).
2. Встановіть і запустіть [Ollama](https://ollama.com).
3. У PowerShell:
   ```powershell
   ollama pull llama3.2
   ollama pull llava
   ```
4. У теці `jarvis` двічі клацніть **`setup.bat`**, дочекайтесь кінця.
5. Запустіть **`start.bat`**.

При першому старті з’явиться майстер налаштування.

## Можливості

| Функція | Опис |
|--------|------|
| Чат | Українська особистість через локальну Ollama |
| Голос | Push-to-talk (`Ctrl+Space`), VAD, опційний wake word «Джарвіс» |
| TTS | Piper (укр.) або запасний espeak/SAPI; переривання `Esc` |
| Програми | Відкрити / перемкнути / закрити, файли, скріншот, введення тексту |
| Vision | Аналіз екрана моделлю `llava` (моніторинг **вимкнено** за замовчуванням) |
| Cursor | Запуск IDE, відкриття проєкту, підготовка промпту (вставка після підтвердження) |
| Пам’ять | SQLite: історія, факти, задачі, налаштування |
| Безпека | Лише дозволений список дій; небезпечні/shell — з підтвердженням; кнопка **STOP** |

## Гарячі клавіші

- `Ctrl+Space` — мікрофон (push-to-talk)
- `Ctrl+M` — mute TTS
- `Ctrl+.` — аварійна STOP
- `Ctrl+,` — налаштування
- `Esc` — зупинити озвучення
- `Enter` — надіслати повідомлення (`Shift+Enter` — новий рядок)

## Український голос (Piper)

1. Завантажте [Piper](https://github.com/rhasspy/piper/releases) і додайте `piper.exe` у PATH.
2. Візьміть українську модель (наприклад з [piper-voices](https://github.com/rhasspy/piper-voices)), файли `*.onnx` + `*.onnx.json`.
3. Покладіть їх у:
   ```
   %LOCALAPPDATA%\JarvisAssistant\voices\
   ```
4. У **Налаштування → Голос** вкажіть ім’я моделі (без шляху) або залиште автопошук першого `.onnx`.

Без Piper JARVIS спробує `espeak-ng` / Windows SAPI (якість української може бути гіршою).

## Структура

```
jarvis/
  main.py                 # точка входу
  setup.bat               # встановлення залежностей
  start.bat               # запуск з Python (.venv)
  build_exe.bat           # збірка Windows .exe (одна команда)
  build_exe_console.bat   # debug .exe з консоллю
  JarvisAssistant.spec    # конфіг PyInstaller
  requirements.txt
  config/                 # налаштування + шляхи для frozen
  core/                   # Ollama, асистент, дії
  voice/                  # STT / TTS / VAD / wake word
  automation/             # програми, файли, Cursor, безпека
  vision/                 # скрін + аналіз
  ui/                     # PySide6 інтерфейс
  database/               # SQLite
  packaging/              # verify, іконка, інструкції dist
  tests/
```

Дані користувача: `%LOCALAPPDATA%\JarvisAssistant\` (`jarvis.db`, `screenshots`, `voices`, `logs`).

## Збірка Windows `.exe`

**На Windows** (у теці `jarvis`) виконайте одну команду:

```bat
build_exe.bat
```

Готовий застосунок: `dist\JarvisAssistant\JarvisAssistant.exe`  
(потрібно копіювати **всю теку** `dist\JarvisAssistant\`, не лише exe).

### Що входить / що ні

| Входить у збірку | Окремо на ПК користувача |
|------------------|---------------------------|
| Код JARVIS, PySide6, клієнтські бібліотеки | **Ollama** (обов’язково) — https://ollama.com |
| | Моделі: `ollama pull llama3.2` (+ `llava`) |
| | Whisper-ваги (завантажаться при першому мікрофоні) |
| | Piper + український `.onnx` (опційно) |

Ollama **навмисно не бандлиться** в exe: окремий сервіс, великі моделі, своє GPU/CPU-ядро. Це нормальна схема для локальних LLM-асистентів.

Детальніше: [packaging/build_exe.md](packaging/build_exe.md).  
Для щоденної розробки зручніше `start.bat` (без перезбірки exe).

## Тести (розробка)

```bash
cd jarvis
python -m pytest tests/ -q
```

На Linux CI / Cloud Agent повний Windows UI і автоматизація не перевіряються; покриті парсер дій, SQLite, клієнт Ollama (mock), VAD, політики безпеки.

## Обмеження (чесно)

- Повна автоматизація вікон / `pywin32` / автозапуск у реєстрі — **лише Windows**.
- Якість STT залежить від мікрофона й моделі Whisper (`base` за замовчуванням).
- Vision потребує окремої моделі (`llava` тощо) і більше RAM/VRAM.
- `run_shell` ніколи не виконується без явного «Так» і блокує очевидні небезпечні шаблони.
- Моніторинг екрана знімає скріни локально — тримайте індикатор на виду; за замовчуванням **ВИМК**.

## Ліцензія / репозиторій

Код асистента в підтеці `jarvis/` репозиторію `horse-uk.sk`.
