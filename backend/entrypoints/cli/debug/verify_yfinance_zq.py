
import yfinance as yf

try:
    # ZQ=F is often the continuous contract
    # ZQZ24.CBT might be specific. Let's try standard tickers.
    # 30-Day Fed Funds Futures
    ticker = yf.Ticker("ZQ=F") 
    data = ticker.history(period="1mo")
    print("ZQ=F Data:")
    print(data.tail())
except Exception as e:
    print(f"Error: {e}")
