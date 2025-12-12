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

    def calculate_indicators_history(self, candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate indicators and return full history (for charts).
        """
        if not candles or len(candles) < 30:
            return candles or []
            
        try:
            df = pd.DataFrame(candles)
            if 'close' not in df.columns:
                if 'Close' in df.columns: df['close'] = df['Close']
                else: return candles

            close = df['close'].astype(float)
            
            # 1. Moving Averages (MA5, MA10, MA20, MA30, MA60)
            df['ma5'] = close.rolling(window=5).mean()
            df['ma10'] = close.rolling(window=10).mean()
            df['ma20'] = close.rolling(window=20).mean()
            df['ma30'] = close.rolling(window=30).mean()
            df['ma60'] = close.rolling(window=60).mean()
            
            # 2. Bollinger Bands (20, 2)
            # Mid = MA20
            # Upper = Mid + 2*std
            # Lower = Mid - 2*std
            std20 = close.rolling(window=20).std()
            df['boll_mid'] = df['ma20']
            df['boll_upper'] = df['boll_mid'] + (std20 * 2)
            df['boll_lower'] = df['boll_mid'] - (std20 * 2)

            # 3. MACD (12, 26, 9)
            # DIF = EMA(12) - EMA(26)
            # DEA = EMA(DIF, 9)
            # BAR = 2 * (DIF - DEA) or just DIF - DEA depending on convention. 
            # Recharts looks for macd_bar.
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            df['macd_dif'] = exp1 - exp2
            df['macd_dea'] = df['macd_dif'].ewm(span=9, adjust=False).mean()
            df['macd_bar'] = 2 * (df['macd_dif'] - df['macd_dea'])
            
            # 4. RSI (14)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi14'] = 100 - (100 / (1 + rs))
            
            # 5. KDJ (Classic: 9, 3, 3)
            # RSV = (Close - Low_9) / (High_9 - Low_9) * 100
            if 'high' in df.columns and 'low' in df.columns:
                low_list = df['low'].rolling(window=9, min_periods=9).min()
                high_list = df['high'].rolling(window=9, min_periods=9).max()
                
                # Check for zero text division
                rsv = (close - low_list) / (high_list - low_list) * 100
                
                # K = 2/3 * PrevK + 1/3 * RSV
                df['kdj_k'] = rsv.ewm(com=2, adjust=False).mean() 
                df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
                df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

            # Fill NaNs
            df = df.replace({np.nan: None})
            
            return df.to_dict(orient='records')
            
        except Exception as e:
            logger.error(f"History calculation failed: {e}")
            return candles # Return original data on error

if __name__ == "__main__":
    # Test logic
    data = [{'close': 100 + i + (i%5)*2} for i in range(100)]
    tool = TechnicalAnalysisTool()
    print(tool.calculate_indicators(data))
