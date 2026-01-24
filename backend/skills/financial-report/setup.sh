#!/bin/bash
# Try to create venv with python3.12 if available, else python3
PYTHON_CMD="python3"
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
fi

echo "Using Python: $PYTHON_CMD"

# Clean existing venv to avoid version mismatch
rm -rf .venv

$PYTHON_CMD -m venv .venv
if [ $? -eq 0 ]; then
    source .venv/bin/activate
    # Upgrade pip to ensure smooth installation
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Setup complete. Activate with 'source .venv/bin/activate'"
else
    echo "Venv creation failed. Installing to user scope..."
    $PYTHON_CMD -m pip install -r requirements.txt
    echo "Setup complete. Dependencies installed in user scope."
fi
