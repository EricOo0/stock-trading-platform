# News & Sentiment Skill

This skill provides tools for retrieving financial news and social media sentiment.

## Requirements
- Python 3.10+
- Internet access (for Sina Finance, Twitter, Reddit)

## Tools

### 1. `news`
Search for financial news related to a specific stock symbol.

- **Arguments**:
  - `symbol` (str): Stock symbol (e.g., '000001', 'sh600001', 'AAPL').
  - `--limit` (int): Max number of results (default: 5).

- **Usage**:
  ```bash
  python scripts/news.py news sh600001 --limit 5
  ```

### 2. `social`
Search for social media discussions (Twitter, Reddit).

- **Arguments**:
  - `query` (str): Search query (e.g., 'TSLA', 'Apple').
  - `--source` (str): Source platform ('twitter', 'reddit', 'all'). Default: 'all'.
  - `--limit` (int): Max number of results per source (default: 5).

- **Usage**:
  ```bash
  python scripts/news.py social "TSLA" --source reddit --limit 3
  ```

### 3. `sentiment`
Analyze the sentiment of a given text.

- **Arguments**:
  - `text` (str): The text to analyze.

- **Usage**:
  ```bash
  python scripts/news.py sentiment "Apple released a great new product today!"
  ```

## Setup

```bash
cd backend/skills/news-sentiment
bash setup.sh
```

## Output Format
All tools output JSON data.
