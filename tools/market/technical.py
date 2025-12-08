import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalysisTool:
    """
    Technical Analysis Tool
    Calculates key technical indicators: MA, RSI, MACD, Bollinger Bands.
    """
    
    def calculate_indicators(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate technical indicators from a list of candles.
        Expected candle format: {'close': float, ...} (from get_historical_data)
        """
        if not candles or len(candles) < 30:
            return {"error": "Insufficient data"}
            
        try:
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            if 'close' not in df.columns:
                 # Try case insensitive mapping if needed, but registry returns 'close'
                 if 'Close' in df.columns: df['close'] = df['Close']
                 else: return {"error": "Missing close price"}
            
            close = df['close'].astype(float)
            
            # 1. Moving Averages
            ma5 = close.rolling(window=5).mean().iloc[-1]
            ma20 = close.rolling(window=20).mean().iloc[-1]
            ma60 = close.rolling(window=60).mean().iloc[-1]
            
            trend = "SIDEWAYS"
            if ma5 > ma20 > ma60: trend = "UP"
            elif ma5 < ma20 < ma60: trend = "DOWN"
            
            # 2. RSI (14)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # RSI Status
            rsi_status = "NEUTRAL"
            if rsi > 70: rsi_status = "OVERBOUGHT"
            elif rsi < 30: rsi_status = "OVERSOLD"
            
            # 3. MACD (12, 26, 9)
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            
            macd_val = macd_line.iloc[-1]
            signal_val = signal_line.iloc[-1]
            
            macd_signal = "NEUTRAL"
            if macd_val > signal_val: macd_signal = "GOLDEN_CROSS" # Bullish
            elif macd_val < signal_val: macd_signal = "DEATH_CROSS" # Bearish
            
            # 4. Bollinger Bands (20, 2)
            ma20_series = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            upper_band = ma20_series + (std20 * 2)
            lower_band = ma20_series - (std20 * 2)
            
            curr_price = close.iloc[-1]
            bb_status = "NORMAL"
            if curr_price > upper_band.iloc[-1]: bb_status = "ABOVE_UPPER"
            elif curr_price < lower_band.iloc[-1]: bb_status = "BELOW_LOWER"

            return {
                "trend": {
                    "status": trend,
                    "ma5": round(ma5, 2),
                    "ma20": round(ma20, 2),
                    "ma60": round(ma60, 2)
                },
                "rsi": {
                    "value": round(rsi, 2),
                    "status": rsi_status
                },
                "macd": {
                    "macd": round(macd_val, 4),
                    "signal": round(signal_val, 4),
                    "status": macd_signal
                },
                "bollinger": {
                    "upper": round(upper_band.iloc[-1], 2),
                    "lower": round(lower_band.iloc[-1], 2),
                    "status": bb_status
                }
            }
            
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test logic
    data = [{'close': 100 + i + (i%5)*2} for i in range(100)]
    tool = TechnicalAnalysisTool()
    print(tool.calculate_indicators(data))
