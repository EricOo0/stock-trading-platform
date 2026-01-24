# Market Data Skill

Provides real-time quotes, historical K-lines, fund flow, sector data, and market turnover for A-share, HK, and US markets.

## Capabilities

-   **Quotes**: Real-time price, volume, change for Stocks, ETFs, and Indices.
-   **K-Line**: Historical OHLCV data (Daily/Weekly/Monthly).
-   **Indices**: Bulk fetch key indices (CN/HK/US).
-   **Sectors**: Industry/Concept rankings and constituent stocks.
-   **Fund Flow**: North/South water, individual stock flow.
-   **Turnover**: Total market turnover (A-share).

## Usage

### CLI

```bash
# Setup
./setup.sh
source .venv/bin/activate

# Get Quote
python scripts/market_data.py quote 600036
python scripts/market_data.py quote 上证指数

# Get Bulk Indices
python scripts/market_data.py indices CN

# Get K-Line (Limit 20)
python scripts/market_data.py kline 600036 --period daily --limit 20

# Get Sector Ranking
python scripts/market_data.py rank --type industry --limit 10

# Get Sector Constituents
python scripts/market_data.py constituents "酿酒行业" --limit 10

# Get Market Turnover
python scripts/market_data.py turnover
```

### Python Import

```python
from scripts.market_data import MarketDataSkill

skill = MarketDataSkill()
quote = skill.get_quote("600036")
kline = skill.get_kline("600036", limit=100)
```
