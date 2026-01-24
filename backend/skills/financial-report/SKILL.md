---
name: financial-report
description: 提供财务指标获取、财报检索与内容访问能力，覆盖A股/美股/港股，适合基本面分析与公司研究。
---
# Financial Report Skill

This skill provides financial data analysis and report retrieval capabilities for global stock markets (A-share, US, HK).

## Features
- **Financial Indicators**: Get key financial metrics (Revenue, Profit, Cashflow, Debt, Valuation)
- **Report Search**: Find latest annual/quarterly reports (10-K/10-Q for US, Annual Reports for A-share/HK)
- **Report Content**: Download and access report content (Text/HTML)

## Usage

### Setup
```bash
bash setup.sh
```

### CLI Examples

**Get Financial Indicators:**
```bash
.venv/bin/python scripts/finance.py indicators AAPL
.venv/bin/python scripts/finance.py indicators 600036
```

**Search Reports:**
```bash
.venv/bin/python scripts/finance.py search AAPL
.venv/bin/python scripts/finance.py search 600036
```

**Get Report Content:**
```bash
.venv/bin/python scripts/finance.py content "http://example.com/report.pdf"
```

## Dependencies
- akshare (A-share data)
- yfinance (US/HK data)
- edgartools (SEC filings)
- requests, pandas
