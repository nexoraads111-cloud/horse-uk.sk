JARVIS AI Assistant — зібрана версія (.exe)
==========================================

Запуск
------
1. Відкрийте теку JarvisAssistant
2. Запустіть JarvisAssistant.exe
3. Перший запуск може завантажити модель Whisper у кеш користувача (потрібен інтернет)

ОБОВ'ЯЗКОВО окремо (не входить у exe)
------------------------------------
• Ollama — https://ollama.com
  Після встановлення:
    ollama pull llama3.2
    ollama pull llava          (для аналізу екрана)

• (Опційно) Piper TTS + український голос .onnx
  Покладіть у: %LOCALAPPDATA%\JarvisAssistant\voices\

Дані програми
-------------
%LOCALAPPDATA%\JarvisAssistant\
  jarvis.db, logs\, screenshots\, voices\

Якщо exe не стартує
-------------------
• Зберіть debug-версію з консоллю: build_exe_console.bat
• Або запускайте через start.bat з вихідного коду (надійніше для оновлень)

Антивірус іноді блокує свіжі PyInstaller-збірки — додайте виняток для теки dist.
