---
name: macro-economy
description: 提供中美宏观数据（GDP、CPI、PMI等）、全球风险指标（VIX、10Y、DXY等）与经济日历事件，适合宏观监控与投研背景信息。
---
# Macro Economy Skill

Provides macro economic data for China and US, global market risk indicators, and economic calendar events.

## Features

- **China Macro Data**: GDP, CPI, PMI, PPI, M2, LPR
- **US Macro Data**: CPI, Unemployment Rate, Interest Rate
- **Market Risk**: VIX, US 10Y Yield, DXY (Dollar Index), Gold, Crude Oil
- **Economic Calendar**: Major economic events and data releases

## Usage

### Setup
```bash
bash setup.sh
```

### CLI Examples

**Get China GDP:**
```bash
.venv/bin/python scripts/macro.py cn_macro GDP
```

**Get China CPI:**
```bash
.venv/bin/python scripts/macro.py cn_macro CPI
```

**Get US Macro (CPI):**
```bash
.venv/bin/python scripts/macro.py us_macro CPI
```

**Get Market Risk Indicators:**
```bash
.venv/bin/python scripts/macro.py risk
```

**Get Economic Calendar (Today):**
```bash
.venv/bin/python scripts/macro.py calendar
```

**Get Economic Calendar (Specific Date):**
```bash
.venv/bin/python scripts/macro.py calendar --date 20240101
```

## Dependencies

- akshare
- yfinance
- pandas
