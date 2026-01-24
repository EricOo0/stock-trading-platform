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

# Install textblob corpora if needed (optional, often handled on first run or skipped)
# python -m textblob.download_corpora

echo "Setup complete. Activate with: source .venv/bin/activate"
