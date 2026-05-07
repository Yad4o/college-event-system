@echo off
REM Usage: activate
REM Activates the project virtual environment on Windows.

if not exist "venv\" (
    echo Virtual environment not found. Run "bash setup.sh" or create it manually.
    exit /b 1
)

call venv\Scripts\activate
echo Virtual environment activated.
