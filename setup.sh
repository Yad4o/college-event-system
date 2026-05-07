#!/bin/bash
# setup.sh — Creates a Python 3.11 virtual environment and installs all dependencies.
# Run once when cloning the repo for the first time.
# Usage: bash setup.sh

set -e

echo "Checking for Python 3.11..."
if ! command -v python3.11 &>/dev/null; then
  echo "ERROR: Python 3.11 not found. Install it from https://www.python.org/downloads/"
  exit 1
fi

echo "Creating virtual environment with Python 3.11..."
python3.11 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip --quiet

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✓ Setup complete!"
echo ""
echo "  To activate the environment, run:"
echo "    source activate        (Linux / Mac)"
echo "    activate.bat           (Windows CMD)"
echo ""
echo "  To start the server:"
echo "    uvicorn app.main:app --reload"
echo ""
echo "  To run tests:"
echo "    pytest"
echo ""
