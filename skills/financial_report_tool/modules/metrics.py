import yfinance as yf
import pandas as pd
import akshare as ak
from typing import Dict, Any, List
from loguru import logger
from .market import detect_market

def get_financial_metrics(symbol: str) -> Dict[str, Any]:
    """
    Fetches key financial metrics (Revenue, Net Income, etc.) for the last few years.
    Supports US, HK, and A-share stocks via yfinance (primary) and AkShare (HK fallback).
    """
    try:
        market, normalized_symbol = detect_market(symbol)
        logger.info(f"Fetching financial metrics for {symbol} (Market: {market}, Normalized: {normalized_symbol})")
        
        metrics = []
        currency = "USD"
        
        # For yfinance, we need the proper suffix
        if market == 'A-SHARE':
            # Determine exchange (Shanghai or Shenzhen)
            if normalized_symbol.startswith('6'):
                yf_symbol = f"{normalized_symbol}.SS"
            else:
                yf_symbol = f"{normalized_symbol}.SZ"
        elif market == 'HK':
            yf_symbol = normalized_symbol if '.HK' in normalized_symbol else f"{normalized_symbol}.HK"
        else:
            yf_symbol = normalized_symbol
        
        # 1. Try yfinance first
        try:
            ticker = yf.Ticker(yf_symbol)
            
            # Get Financials (Income Statement)
            financials = ticker.financials
            if not financials.empty:
                currency = ticker.info.get("currency", "USD")
                financials_T = financials.T
                financials_T.sort_index(inplace=True)
                
                for date, row in financials_T.iterrows():
                    item = {
                        "date": date.strftime("%Y-%m-%d"),
                        "revenue": row.get("Total Revenue", 0),
                        "net_income": row.get("Net Income", 0),
                        "gross_profit": row.get("Gross Profit", 0),
                        "operating_income": row.get("Operating Income", 0)
                    }
                    # Handle NaN
                    for k, v in item.items():
                        if pd.isna(v):
                            item[k] = 0
                    metrics.append(item)
        except Exception as e:
            logger.warning(f"yfinance fetch failed for {symbol}: {e}")

        # 2. If metrics empty and HK, try AkShare fallback
        if not metrics and market == 'HK':
            try:
                logger.info(f"Trying AkShare metrics fallback for {symbol}")
                code = normalized_symbol.replace('.HK', '').strip()
                if len(code) == 4 and code.isdigit():
                    code = '0' + code
                
                df = ak.stock_financial_hk_analysis_indicator_em(symbol=code)
                if not df.empty:
                    currency = "HKD"
                    # Take latest 5
                    df = df.head(5)
                    
                    for _, row in df.iterrows():
                        # REPORT_DATE format varies, assume standard
                        r_date = pd.to_datetime(row['REPORT_DATE'])
                        
                        item = {
                            "date": r_date.strftime("%Y-%m-%d"),
                            "revenue": float(row['OPERATE_INCOME']) if not pd.isna(row['OPERATE_INCOME']) else 0,
                            "net_income": float(row['HOLDER_PROFIT']) if not pd.isna(row['HOLDER_PROFIT']) else 0,
                            # Gross profit not directly available in this indicator API, set to 0 or calculate if ratio available
                            # GROSS_PROFIT_RATIO is available
                            "gross_profit": 0, 
                            "operating_income": 0
                        }
                        metrics.append(item)
            except Exception as e:
                logger.error(f"AkShare metrics fallback failed: {e}")

        if not metrics:
            logger.warning(f"No financial data found for {yf_symbol}")
            return {
                "status": "error", 
                "message": "No financial data found",
                "market": market,
                "symbol": normalized_symbol
            }

        return {
            "status": "success",
            "symbol": normalized_symbol,
            "market": market,
            "normalized_symbol": yf_symbol,
            "currency": currency,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Error fetching financial metrics for {symbol}: {e}")
        return {"status": "error", "message": str(e), "market": "unknown"}

def get_financial_indicators(symbol: str, years: int = 3) -> Dict[str, Any]:
    """
    获取财务指标数据 (5大类指标)
    
    Args:
        symbol: 股票代码
        years: 获取年数 (默认3年)
    
    Returns:
        财务指标数据字典
    """
    try:
        # 检测市场类型
        market, normalized_symbol = detect_market(symbol)
        logger.info(f"Fetching financial indicators for {symbol} (Market: {market})")
        
        indicators = {}
        data_source = "unknown"
        
        # 根据市场选择数据源
        if market == 'A-SHARE':
            try:
                from ..data_sources.akshare_financial import AkShareFinancialSource
            except ImportError:
                # Fallback for direct execution or different path structure
                try:
                    from skills.financial_report_tool.data_sources.akshare_financial import AkShareFinancialSource
                except ImportError:
                    from data_sources.akshare_financial import AkShareFinancialSource
            
            source = AkShareFinancialSource()
            # AkShare uses 6 digit code
            ak_symbol = normalized_symbol
            if '.' in ak_symbol:
                ak_symbol = ak_symbol.split('.')[0]
                
            indicators = source.get_financial_indicators(ak_symbol, years)
            
            # 如果AkShare没有数据，尝试使用yfinance作为fallback
            if not indicators or all(
                indicators.get(cat, {}).get(key) in [None, 0, 0.0] 
                for cat in ['revenue', 'profit', 'cashflow', 'debt', 'shareholder_return']
                for key in indicators.get(cat, {}).keys()
            ):
                logger.warning(f"AkShare returned no data for {normalized_symbol}, trying yfinance fallback")
                try:
                    from ..data_sources.yfinance_financial import YFinanceFinancialSource
                except ImportError:
                    try:
                        from skills.financial_report_tool.data_sources.yfinance_financial import YFinanceFinancialSource
                    except ImportError:
                        from data_sources.yfinance_financial import YFinanceFinancialSource
                
                # 确定交易所后缀
                if normalized_symbol.startswith('6'):
                    yf_symbol = f"{normalized_symbol}.SS"  # 上海
                else:
                    yf_symbol = f"{normalized_symbol}.SZ"  # 深圳
                
                yf_source = YFinanceFinancialSource()
                indicators = yf_source.get_financial_indicators(yf_symbol, years)
                data_source = "yfinance (fallback)"
            else:
                data_source = "AkShare"
            
        elif market in ['US', 'HK']:
            try:
                from ..data_sources.yfinance_financial import YFinanceFinancialSource
            except ImportError:
                try:
                    from skills.financial_report_tool.data_sources.yfinance_financial import YFinanceFinancialSource
                except ImportError:
                    from data_sources.yfinance_financial import YFinanceFinancialSource
                    
            source = YFinanceFinancialSource()
            
            # Get yfinance symbol
            yf_symbol = normalized_symbol
            if market == 'HK' and not yf_symbol.endswith('.HK'):
                yf_symbol = f"{yf_symbol}.HK"
                
            indicators = source.get_financial_indicators(yf_symbol, years)
            data_source = "yfinance"
            
        else:
            logger.error(f"Unknown market type: {market}")
            return {
                "status": "error",
                "message": f"Unsupported market type: {market}",
                "symbol": symbol,
                "market": market
            }
        
        # 验证数据是否有效（不为空）
        if not indicators or not any(indicators.values()):
            logger.warning(f"No valid indicators data for {symbol}")
            return {
                "status": "error",
                "message": "No financial indicators data available",
                "symbol": symbol,
                "market": market,
                "data_source": data_source
            }
        
        # 构建响应
        from datetime import datetime
        response = {
            "status": "success",
            "symbol": symbol,
            "market": market,
            "data_source": data_source,
            "indicators": indicators,
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching financial indicators for {symbol}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "symbol": symbol
        }

def fetch_financial_data_as_text(symbol: str, market: str) -> str:
    """
    Fetches financial data from yfinance and formats it as text for LLM analysis.
    Used as a fallback when full report text is not available.
    """
    content_parts = []
    
    # 1. Try yfinance first
    try:
        # Get normalized symbol for yfinance
        if market == 'HK' and not symbol.endswith('.HK'):
            yf_symbol = f"{symbol}.HK"
        elif market == 'A-SHARE':
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            else:
                yf_symbol = f"{symbol}.SZ"
        else:
            yf_symbol = symbol
            
        ticker = yf.Ticker(yf_symbol)
        
        # Business Summary
        info = ticker.info
        if info and 'longBusinessSummary' in info:
            content_parts.append(f"=== Business Summary ===\n{info['longBusinessSummary']}\n")
            
        # Financial Statements (Last 3 years/periods)
        # Income Statement
        try:
            financials = ticker.financials
            if not financials.empty:
                content_parts.append(f"=== Income Statement (Recent) ===\n{financials.iloc[:, :3].to_string()}\n")
        except Exception:
            pass
            
        # Balance Sheet
        try:
            balance_sheet = ticker.balance_sheet
            if not balance_sheet.empty:
                content_parts.append(f"=== Balance Sheet (Recent) ===\n{balance_sheet.iloc[:, :3].to_string()}\n")
        except Exception:
            pass
            
        # Cash Flow
        try:
            cashflow = ticker.cashflow
            if not cashflow.empty:
                content_parts.append(f"=== Cash Flow (Recent) ===\n{cashflow.iloc[:, :3].to_string()}\n")
        except Exception:
            pass
            
        # Major Holders
        try:
            major_holders = ticker.major_holders
            if major_holders is not None and not major_holders.empty:
                content_parts.append(f"=== Major Holders ===\n{major_holders.to_string()}\n")
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Error fetching yfinance data for {symbol}: {e}")

    # 2. If content is weak (e.g. rate limited or empty) and it's HK, try AkShare
    # Check if we have enough data. If we only have Business Summary or nothing, try AkShare for financials.
    has_financials = any("Income Statement" in p or "Balance Sheet" in p for p in content_parts)
    
    if not has_financials and market == 'HK':
        try:
            logger.info(f"Fetching HK financial data from AkShare for {symbol}")
            ak_content = _fetch_hk_financial_data_akshare(symbol)
            if ak_content:
                content_parts.append(ak_content)
        except Exception as e:
            logger.error(f"Error fetching AkShare data for {symbol}: {e}")

    return "\n".join(content_parts)

def _fetch_hk_financial_data_akshare(symbol: str) -> str:
    """Fetch HK financial indicators using AkShare"""
    try:
        # Normalize symbol for AkShare (e.g., "0700.HK" -> "00700")
        code = symbol.replace('.HK', '').strip()
        # Ensure 5 digits with leading zeros if needed, though input is usually already normalized
        # But safe to check. If it's 4 digits like 0700, make it 00700.
        if len(code) == 4 and code.isdigit():
            code = '0' + code
        
        df = ak.stock_financial_hk_analysis_indicator_em(symbol=code)
        if df.empty:
            return ""
        
        # Take the latest 5 reports
        latest = df.head(5)
        
        output = "=== Financial Indicators (AkShare Source) ===\n"
        output += "Note: Values in HKD or standard units.\n"
        
        # Select useful columns
        # OPERATE_INCOME: Revenue
        # HOLDER_PROFIT: Net Profit
        # BASIC_EPS: EPS
        # ROE_AVG: ROE
        # GROSS_PROFIT_RATIO: Gross Margin
        cols_map = {
            'REPORT_DATE': 'Date',
            'OPERATE_INCOME': 'Revenue',
            'OPERATE_INCOME_YOY': 'Revenue_YoY%',
            'HOLDER_PROFIT': 'Net_Income',
            'HOLDER_PROFIT_YOY': 'Net_Income_YoY%',
            'BASIC_EPS': 'EPS',
            'ROE_AVG': 'ROE%',
            'GROSS_PROFIT_RATIO': 'Gross_Margin%'
        }
        
        existing_cols = [c for c in cols_map.keys() if c in df.columns]
        subset = latest[existing_cols].copy()
        subset.rename(columns=cols_map, inplace=True)
        
        output += subset.to_string(index=False) + "\n"
        return output
        
    except Exception as e:
        logger.error(f"AkShare HK data error: {e}")
        return ""
