@echo off
REM Stadium V3 Windows Client - Launch Script
REM Este script debe ejecutarse desde la carpeta winClient

echo [*] Launching Stadium V3...
echo [*] Working Directory: %CD%

REM Activate virtual environment (if exists)
if exist venv\Scripts\activate.bat (
    echo [*] Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run main.py
python main.py

pause
