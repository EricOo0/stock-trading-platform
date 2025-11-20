# Sentiment Analysis Tool - Installation Guide

## Dependencies

This skill requires the following Python packages:
- `transformers` (Hugging Face Transformers library)
- `torch` (PyTorch)

## Installation

### Option 1: Using pip (with virtual environment - Recommended)

```bash
# Create virtual environment if not exists
python3 -m venv ../../venv

# Activate virtual environment
source ../../venv/bin/activate

# Install dependencies
pip install transformers torch

# Or install from requirements file
pip install -r requirements.txt
```

### Option 2: Using pip with --user flag

```bash
pip3 install --user transformers torch
```

### Option 3: Using conda

```bash
conda install -c conda-forge transformers pytorch
```

## Model Download

On first use, FinBERT model will be automatically downloaded from Hugging Face Hub:
- Model: `ProsusAI/finbert`
- Size: ~440MB
- Cache location: `~/.cache/huggingface/`

**Note**: First run may take 1-2 minutes to download the model.

## Testing

```bash
# Run test script
python3 test_skill.py
```

Expected output should show "method": "finbert" in the analysis results.

## Fallback Behavior

If FinBERT cannot be loaded (missing dependencies), the skill will:
1. Log a warning message
2. Automatically fallback to heuristic sentiment analysis
3. Continue functioning (with lower accuracy)

This ensures the skill is always operational.

## Troubleshooting

### Error: "No module named 'transformers'"
**Solution**: Install transformers library (see Installation section above)

### Error: "No module named 'torch'"
**Solution**: Install PyTorch (see Installation section above)

### Error: "Failed to download model"
**Solution**: 
- Check internet connection
- Verify Hugging Face Hub is accessible
- Try manual download: `huggingface-cli download ProsusAI/finbert`

### Model loading is slow
**Explanation**: First run downloads ~440MB model. Subsequent runs load from cache and are much faster.

## System Requirements

- Python 3.8+
- ~500MB disk space (for model cache)
- ~2GB RAM (during model loading)
- Internet connection (for first-time model download)
