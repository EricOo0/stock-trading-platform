#!/bin/bash
set -e

# Clean previous venv
rm -rf .venv

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "Setup complete. Activate with: source .venv/bin/activate"
echo "Remember to set TAVILY_API_KEY environment variable."
