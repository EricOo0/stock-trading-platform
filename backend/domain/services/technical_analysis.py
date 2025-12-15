import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalysisTool:
    """
    Technical Analysis Tool
    Calculates key technical indicators: MA, EMA, RSI, MACD, Bollinger Bands, KDJ, ATR, OBV, Pivot Points.
    """
    
    def calculate_indicators(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate technical indicators from a list of candles (Basic version for legacy compatibility).
        """
        # Reuse advanced calculation but return simplified format
        advanced = self.calculate_advanced_indicators(candles)
        if "error" in advanced:
            return advanced
            
        # Extract legacy format
        tech = advanced.get("technical_indicators", {})
        trend = tech.get("trend", {})
        rsi = tech.get("momentum", {}).get("rsi_14", 50)
        macd = tech.get("momentum", {}).get("macd", {})
        boll = tech.get("volatility", {}).get("boll", {})
        
        # Simple trend mapping
        ma_status = trend.get("status", "SIDEWAYS")
        trend_status = "SIDEWAYS"
        if ma_status == "bullish_alignment": trend_status = "UP"
        elif ma_status == "bearish_alignment": trend_status = "DOWN"

        # Simple RSI mapping
        rsi_status = "NEUTRAL"
        if rsi > 70: rsi_status = "OVERBOUGHT"
        elif rsi < 30: rsi_status = "OVERSOLD"

        # Simple BB mapping
        bb_status = "NORMAL"
        if boll.get("position") == "above_upper": bb_status = "ABOVE_UPPER"
        elif boll.get("position") == "below_lower": bb_status = "BELOW_LOWER"

        return {
            "trend": {
                "status": trend_status,
                "ma5": trend.get("ma_system", {}).get("ma5"),
                "ma20": trend.get("ma_system", {}).get("ma20"),
                "ma60": trend.get("ma_system", {}).get("ma60")
            },
            "rsi": {
                "value": rsi,
                "status": rsi_status
            },
            "macd": {
                "macd": macd.get("dif"),
                "signal": macd.get("dea"),
                "status": macd.get("cross_signal", "NEUTRAL").upper()
            },
            "bollinger": {
                "upper": boll.get("upper"),
                "lower": boll.get("lower"),
                "status": bb_status
            }
        }

    def calculate_advanced_indicators(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive technical indicators for Agent Context.
        Includes: EMA, ATR, OBV, Pivot Points, Price Action.
        """
        if not candles or len(candles) < 30:
            return {"error": "Insufficient data"}
            
        try:
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            # Normalize columns
            col_map = {c: c.lower() for c in df.columns}
            df = df.rename(columns=col_map)
            
            required = ['close', 'high', 'low']
            if not all(col in df.columns for col in required):
                 # Try fallback for volume if missing
                 if 'volume' not in df.columns: df['volume'] = 0
                 # Check again for price cols
                 if not all(col in df.columns for col in ['close', 'high', 'low']):
                     return {"error": "Missing price data (high/low/close)"}
            
            # Type conversion
            for col in ['close', 'high', 'low']:
                df[col] = df[col].astype(float)
            if 'volume' in df.columns:
                df['volume'] = df['volume'].astype(float)
            else:
                df['volume'] = 0.0
            
            close = df['close']
            high = df['high']
            low = df['low']
            vol = df['volume']
            
            # --- 1. Trend Indicators ---
            # SMA
            ma5 = close.rolling(window=5).mean().iloc[-1]
            ma10 = close.rolling(window=10).mean().iloc[-1]
            ma20 = close.rolling(window=20).mean().iloc[-1]
            ma60 = close.rolling(window=60).mean().iloc[-1]
            
            # EMA (Exponential) - More sensitive
            ema12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
            ema26 = close.ewm(span=26, adjust=False).mean().iloc[-1]
            
            # Trend Status
            ma_status = "sideways"
            if ma5 > ma10 > ma20 > ma60: ma_status = "bullish_alignment"
            elif ma5 < ma10 < ma20 < ma60: ma_status = "bearish_alignment"

            # --- 2. Momentum Indicators ---
            # RSI (14)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]
            
            # MACD (12, 26, 9)
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd_dif = exp1 - exp2
            macd_dea = macd_dif.ewm(span=9, adjust=False).mean()
            macd_hist = 2 * (macd_dif - macd_dea)
            
            dif_val = macd_dif.iloc[-1]
            dea_val = macd_dea.iloc[-1]
            hist_val = macd_hist.iloc[-1]
            
            # MACD Signal
            cross_signal = "neutral"
            if len(macd_dif) > 2:
                if macd_dif.iloc[-1] > macd_dea.iloc[-1] and macd_dif.iloc[-2] <= macd_dea.iloc[-2]:
                    cross_signal = "golden_cross"
                elif macd_dif.iloc[-1] < macd_dea.iloc[-1] and macd_dif.iloc[-2] >= macd_dea.iloc[-2]:
                    cross_signal = "death_cross"
                elif dif_val > dea_val:
                    cross_signal = "bullish_zone"
                else:
                    cross_signal = "bearish_zone"
            
            # --- 3. Volatility ---
            # Bollinger Bands
            std20 = close.rolling(window=20).std()
            ma20_series = close.rolling(window=20).mean()
            upper = ma20_series + 2 * std20
            lower = ma20_series - 2 * std20
            width_pct = (upper - lower) / ma20_series
            
            curr_price = close.iloc[-1]
            bb_pos = "within_bands"
            if curr_price > upper.iloc[-1]: bb_pos = "above_upper"
            elif curr_price < lower.iloc[-1]: bb_pos = "below_lower"
            
            # ATR (14)
            high_low = high - low
            high_close = (high - close.shift()).abs()
            low_close = (low - close.shift()).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]

            # --- 4. Volume Analysis ---
            # OBV
            obv_change = pd.Series(0, index=df.index)
            obv_change.loc[close > close.shift()] = vol
            obv_change.loc[close < close.shift()] = -vol # Use negative for obv calculation logic
            obv = obv_change.cumsum()
            
            obv_slope = "flat"
            if len(obv) > 5:
                if obv.iloc[-1] > obv.iloc[-5]: obv_slope = "rising"
                elif obv.iloc[-1] < obv.iloc[-5]: obv_slope = "falling"

            # Volume MA
            vol_ma5 = vol.rolling(window=5).mean().iloc[-1]
            vol_ratio = vol.iloc[-1] / vol_ma5 if vol_ma5 > 0 else 0

            # --- 5. Support / Resistance (Pivot Points) ---
            prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
            pp = (prev['high'] + prev['low'] + prev['close']) / 3
            r1 = 2 * pp - prev['low']
            s1 = 2 * pp - prev['high']
            
            high_20d = high.tail(20).max()
            low_20d = low.tail(20).min()

            # --- 6. Recent Price Action ---
            recent_data = df.tail(15).copy()
            if 'date' in df.columns:
                 recent_data['date_str'] = df['date'].tail(15).astype(str)
            else:
                 recent_data['date_str'] = [f"T-{i}" for i in range(len(recent_data)-1, -1, -1)]

            price_action = []
            for _, row in recent_data.iterrows():
                price_action.append({
                    "date": row.get('date_str', ''),
                    "open": round(float(row['open']), 2),
                    "high": round(float(row['high']), 2),
                    "low": round(float(row['low']), 2),
                    "close": round(float(row['close']), 2),
                    "volume": float(row['volume'])
                })

            context = {
                "market_status": {
                    "current_price": round(curr_price, 2),
                    "daily_change_pct": round((curr_price - close.iloc[-2]) / close.iloc[-2] * 100, 2) if len(close) > 1 else 0,
                    "volume_ratio": round(vol_ratio, 2)
                },
                "recent_price_action": price_action,
                "technical_indicators": {
                    "trend": {
                        "ma_system": {
                            "ma5": round(ma5, 2),
                            "ma10": round(ma10, 2),
                            "ma20": round(ma20, 2),
                            "ma60": round(ma60, 2)
                        },
                        "ema_system": {
                            "ema12": round(ema12, 2),
                            "ema26": round(ema26, 2)
                        },
                        "status": ma_status
                    },
                    "momentum": {
                        "rsi_14": round(rsi_val, 2),
                        "macd": {
                            "dif": round(dif_val, 3),
                            "dea": round(dea_val, 3),
                            "hist": round(hist_val, 3),
                            "cross_signal": cross_signal
                        }
                    },
                    "volatility": {
                        "atr_14": round(atr, 2),
                        "boll": {
                            "upper": round(upper.iloc[-1], 2),
                            "lower": round(lower.iloc[-1], 2),
                            "width_pct": round(width_pct.iloc[-1], 4),
                            "position": bb_pos
                        }
                    },
                    "volume_analysis": {
                        "obv_slope": obv_slope,
                        "current_vol_vs_ma5": round(vol_ratio, 2)
                    }
                },
                "support_resistance": {
                    "pivot_points": {
                        "pivot": round(pp, 2),
                        "r1": round(r1, 2),
                        "s1": round(s1, 2)
                    },
                    "recent_extremes": {
                        "high_20d": round(high_20d, 2),
                        "low_20d": round(low_20d, 2)
                    }
                }
            }
            
            return context

        except Exception as e:
            logger.error(f"Advanced analysis failed: {e}", exc_info=True)
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
            std20 = close.rolling(window=20).std()
            df['boll_mid'] = df['ma20']
            df['boll_upper'] = df['boll_mid'] + (std20 * 2)
            df['boll_lower'] = df['boll_mid'] - (std20 * 2)

            # 3. MACD (12, 26, 9)
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
            
            # 5. KDJ
            if 'high' in df.columns and 'low' in df.columns:
                low_list = df['low'].rolling(window=9, min_periods=9).min()
                high_list = df['high'].rolling(window=9, min_periods=9).max()
                rsv = (close - low_list) / (high_list - low_list) * 100
                df['kdj_k'] = rsv.ewm(com=2, adjust=False).mean() 
                df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
                df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

            df = df.replace({np.nan: None})
            return df.to_dict(orient='records')
            
        except Exception as e:
            logger.error(f"History calculation failed: {e}")
            return candles 

if __name__ == "__main__":
    # Test logic
    data = [{'close': 100 + i + (i%5)*2, 'high': 105+i, 'low': 95+i, 'volume': 1000} for i in range(100)]
    tool = TechnicalAnalysisTool()
    print(tool.calculate_advanced_indicators(data))
