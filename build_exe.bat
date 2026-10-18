@echo off
title SeePD BTK Hangasszisztens - EXE Fordito
cd /d "%~dp0"
echo Ellenorzes: PyInstaller telepitese...
python -m pip install pyinstaller
echo.
echo Gyors forditas inditasa (felesleges konyvtarak nelkul)...
python -m PyInstaller --noconsole --onefile --clean --name "SeePD-BTK-VoiceAssistant" ^
  --exclude-module torch ^
  --exclude-module torchvision ^
  --exclude-module scipy ^
  --exclude-module pandas ^
  --exclude-module numba ^
  --exclude-module onnxruntime ^
  --exclude-module cv2 ^
  --exclude-module matplotlib ^
  --hidden-import="pynput.keyboard._win32" ^
  --hidden-import="pynput.mouse._win32" ^
  --hidden-import="pyttsx3.drivers" ^
  --hidden-import="pyttsx3.drivers.sapi5" ^
  --hidden-import="google.generativeai" ^
  --add-data "btk_cache.json;." ^
  --add-data "config.json;." ^
  main.py
echo.
echo ========================================================
echo A kesz futtathato program a 'dist' mappaban talalhato!
echo ========================================================
pause
