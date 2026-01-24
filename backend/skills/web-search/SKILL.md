---
name: web-search
description: 使用 Tavily 提供网页搜索与新闻检索，支持结果数、主题与时间范围配置，适合信息查找与新闻追踪。
---
# Web Search Skill

This skill provides web search capabilities using Tavily.

## Requirements
- Python 3.10+
- `TAVILY_API_KEY` environment variable.

## Tools

### 1. `search`
Search the web for information or news.

- **Arguments**:
  - `query` (str): Search query.
  - `--max_results` (int): Maximum results to return (default: 10).
  - `--topic` (str): 'general' or 'news' (default: 'general').
  - `--days` (int): Days back for news search (default: 10).
  - `--domains` (list): Specific domains to search (optional).

- **Usage**:
  ```bash
  # General search
  python scripts/search.py "latest AI trends" --max_results 5

  # News search
  python scripts/search.py "NVIDIA stock" --topic news --days 3
  
  # Domain specific
  python scripts/search.py "Python 3.12 release" --domains python.org
  ```

## Setup

```bash
cd backend/skills/web-search
bash setup.sh
export TAVILY_API_KEY="tvly-..."
```

## Output Format
JSON list of results with `title`, `href`, `body`, and `score`.
