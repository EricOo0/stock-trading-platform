import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import edgar
from edgar import set_identity, Company
import re
import akshare as ak

class FinancialReportSkill:
    def __init__(self):
        self.name = "financial_report_tool"
        self.description = "Fetches financial report data and documents for companies."
        # Initialize Edgar (identity is required by SEC)
        try:
            set_identity("StockAnalysisAgent <agent@example.com>")
        except Exception as e:
            logger.warning(f"Failed to set edgar identity: {e}")

    def detect_market(self, symbol: str) -> Tuple[str, str]:
        """
        Detect which market the stock belongs to based on symbol format.
        Returns: (market, normalized_symbol)
        
        Markets:
        - 'US': American stocks (e.g., AAPL, TSLA)
        - 'HK': Hong Kong stocks (e.g., 0700.HK, 9988.HK)
        - 'A-SHARE': Chinese A-shares (e.g., 600036.SS, 000001.SZ)
        """
        symbol_upper = symbol.upper()
        
        # Hong Kong stocks
        if '.HK' in symbol_upper:
            return ('HK', symbol_upper)
        
        # A-shares (Shanghai/Shenzhen)
        if '.SS' in symbol_upper or '.SZ' in symbol_upper:
            # Extract the base code for AkShare (e.g., 600036.SS -> 600036)
            base_code = symbol_upper.split('.')[0]
            return ('A-SHARE', base_code)
        
        # Check if it's a pure number (likely Chinese stock without suffix)
        if symbol.isdigit():
            if len(symbol) == 6:
                # Could be A-share or HK
                if symbol.startswith('6'):
                    return ('A-SHARE', symbol)  # Shanghai
                elif symbol.startswith(('0', '3')):
                    return ('A-SHARE', symbol)  # Shenzhen
                else:
                    return ('HK', f"{symbol}.HK")  # Hong Kong
        
        # Default to US stock
        return ('US', symbol_upper)

    def get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches key financial metrics (Revenue, Net Income, etc.) for the last few years.
        Supports US, HK, and A-share stocks via yfinance.
        """
        try:
            market, normalized_symbol = self.detect_market(symbol)
            logger.info(f"Fetching financial metrics for {symbol} (Market: {market}, Normalized: {normalized_symbol})")
            
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
            
            ticker = yf.Ticker(yf_symbol)
            
            # Get Financials (Income Statement)
            financials = ticker.financials
            if financials.empty:
                logger.warning(f"No financial data found for {yf_symbol}")
                return {
                    "status": "error", 
                    "message": "No financial data found",
                    "market": market
                }

            # Extract key metrics
            metrics = []
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

            return {
                "status": "success",
                "symbol": symbol,
                "market": market,
                "normalized_symbol": yf_symbol,
                "currency": ticker.info.get("currency", "USD"),
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"Error fetching financial metrics for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market": "unknown"}

    def get_latest_report(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches metadata about the latest financial report.
        Different strategies for different markets:
        - US: SEC EDGAR (edgartools)
        - HK: Web search for IR page
        - A-Share: AkShare announcement API
        """
        try:
            market, normalized_symbol = self.detect_market(symbol)
            logger.info(f"Fetching latest report for {symbol} (Market: {market})")
            
            if market == 'US':
                # Use SEC EDGAR for US stocks
                return self._get_us_report(normalized_symbol)
            elif market == 'HK':
                # Hong Kong stocks - use web search
                return self._get_hk_report(normalized_symbol)
            elif market == 'A-SHARE':
                # A-share stocks - use AkShare
                return self._get_ashare_report(normalized_symbol)
            else:
                return {
                    "status": "error",
                    "message": "Unknown market type",
                    "market": market
                }

        except Exception as e:
            logger.error(f"Error fetching report for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def _get_us_report(self, symbol: str) -> Dict[str, Any]:
        """Get US stock report from SEC EDGAR"""
        try:
            company = Company(symbol)
            filings = company.get_filings(form=["10-K", "10-Q"]).latest(1)
            
            if not filings:
                return {"status": "error", "message": "No filings found", "market": "US"}
            
            filing = filings
            
            return {
                "status": "success",
                "market": "US",
                "symbol": symbol,
                "form_type": filing.form,
                "filing_date": filing.filing_date,
                "accession_number": filing.accession_number,
                "url": filing.url,
                "download_url": filing.url  # SEC page URL
            }
        except Exception as e:
            logger.error(f"Error fetching US report for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market": "US"}

    def _get_hk_report(self, symbol: str) -> Dict[str, Any]:
        """Get HK stock report via web search"""
        try:
            # Extract stock code (remove .HK suffix)
            stock_code = symbol.replace('.HK', '')
            
            # Common HK company IR pages (Top companies)
            ir_pages = {
                '0700': 'https://www.tencent.com/zh-cn/investors.html',
                '9988': 'https://www.alibabagroup.com/cn/ir/home',
                '0941': 'https://www.cmhk.com/tc/ir/',
                '0388': 'https://www.hkex.com.hk/Investor-Relations',
                '0939': 'https://www.ccbintl.com/investor_relations/',
            }
            
            result = {
                "status": "partial",
                "market": "HK",
                "symbol": symbol,
                "message": "港股财报需要从公司投资者关系页面或披露易获取"
            }
            
            # If we have a known IR page, provide it
            if stock_code in ir_pages:
                result["ir_url"] = ir_pages[stock_code]
                result["download_url"] = ir_pages[stock_code]
                result["status"] = "success"
            
            # Always provide HKEXnews search link
            hkex_search_url = f"https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=zh&searchtype=1&code={stock_code}"
            result["hkexnews_url"] = hkex_search_url
            
            # If no direct IR, use HKEXnews as download URL
            if "download_url" not in result:
                result["download_url"] = hkex_search_url
            
            result["suggestions"] = [
                f"访问披露易搜索: {hkex_search_url}",
                "在搜索结果中查找'年度报告'或'Annual Report'"
            ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching HK report for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market": "HK"}

    def _get_ashare_report(self, symbol: str) -> Dict[str, Any]:
        """Get A-share stock report via direct links"""
        try:
            # For now, provide direct links to cninfo
            # Future: Can implement AkShare API when stable
            
            cninfo_url = f"http://www.cninfo.com.cn/new/disclosure/stock?stockCode={symbol}&orgId="
            
            return {
                "status": "success",
                "market": "A-SHARE",
                "symbol": symbol,
                "message": "请访问巨潮资讯网查看财报",
                "cninfo_url": cninfo_url,
                "download_url": cninfo_url,
                "title": "巨潮资讯网 - 公司公告",
                "suggestions": [
                    f"访问巨潮资讯网: {cninfo_url}",
                    "在页面中筛选'定期报告'查看年报"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error fetching A-share report for {symbol}: {e}")
            cninfo_url = f"http://www.cninfo.com.cn/new/disclosure/stock?stockCode={symbol}"
            return {
                "status": "partial",
                "message": f"获取失败: {str(e)}",
                "market": "A-SHARE",
                "symbol": symbol,
                "cninfo_url": cninfo_url,
                "download_url": cninfo_url,
                "suggestions": [
                    f"访问巨潮资讯网: {cninfo_url}",
                    "手动搜索年度报告"
                ]
            }

    def _get_ashare_report(self, symbol: str) -> Dict[str, Any]:
        """
        Get A-share stock latest annual report PDF link via AkShare.
        """
        # 1. 基础清洗：确保 symbol 是 6 位数字 (去掉可能的 sh/sz 前缀)
        clean_symbol = re.sub(r"\D", "", symbol)
        
        # 构造兜底的通用搜索链接 (万一 API 挂了，用户还能手动点)
        # 巨潮的新版链接通常不需要 orgId 也能模糊搜，但最好只传 stockCode
        fallback_url = f"http://www.cninfo.com.cn/new/disclosure/stock?stockCode={clean_symbol}&orgId="

        try:
            # 2. 调用 AkShare 获取个股公告列表
            # 这是一个网络请求，可能会有延迟，生产环境建议加 cache 或异步处理
            print(f"Fetching report list for {clean_symbol}...")
            df = ak.stock_notice_report(symbol=clean_symbol)
            print(df)
            # 3. 筛选逻辑：找到最新的“年度报告”
            # 这里的筛选非常关键：
            # - 必须包含 "年年度报告" (匹配 2023年年度报告)
            # - 不能包含 "摘要" (我们不要只有几页的 Summary)
            # - 不能包含 "取消" (防止撤回的公告)
            mask = (
                df['公告标题'].str.contains('年年度报告', na=False) & 
                ~df['公告标题'].str.contains('摘要', na=False) &
                ~df['公告标题'].str.contains('取消', na=False)
            )
            
            target_df = df[mask]

            if target_df.empty:
                raise ValueError("未找到年度报告 PDF")

            # 4. 按时间倒序排序，取第一条（最新的）
            # AkShare 返回的数据通常已经是时间倒序，但为了保险起见强制转 datetime 排序
            target_df['公告时间'] = pd.to_datetime(target_df['公告时间'])
            latest_report = target_df.sort_values(by='公告时间', ascending=False).iloc[0]

            title = latest_report['公告标题']
            pdf_url = latest_report['公告URL']
            publish_date = str(latest_report['公告时间'].date())

            # 处理 URL 前缀 (AkShare 有时返回相对路径，有时返回绝对路径，视源而定)
            # 巨潮资讯的 PDF 链接通常需要拼接前缀，如果已经是 http 开头则不用
            if not pdf_url.startswith("http"):
                # 这里的 base url 可能会变，目前巨潮常用的是这个
                final_pdf_url = f"http://static.cninfo.com.cn/{pdf_url}"
            else:
                final_pdf_url = pdf_url

            return {
                "status": "success",
                "market": "A-SHARE",
                "symbol": clean_symbol,
                "message": f"成功获取 {clean_symbol} 最新年报",
                "report_title": title,
                "publish_date": publish_date,
                "download_url": final_pdf_url, # 这是直接的 PDF 下载/预览链接
                "cninfo_url": fallback_url,    # 这是原来的跳转页
                "suggestions": [
                    f"已找到: {title}",
                    "点击 download_url 直接下载 PDF",
                    "如果下载失败，请访问 cninfo_url 手动查找"
                ]
            }

        except Exception as e:
            logger.error(f"Error fetching A-share report for {symbol}: {e}")
            # 发生任何错误（API 挂了、没找到数据），回退到原来的逻辑
            return {
                "status": "partial",
                "message": f"自动拉取失败，请手动访问: {str(e)}",
                "market": "A-SHARE",
                "symbol": clean_symbol,
                "download_url": fallback_url, # 回退到搜索页
                "cninfo_url": fallback_url,
                "suggestions": [
                    f"访问巨潮资讯网: {fallback_url}",
                    "在页面中筛选 '定期报告' -> '年报'"
                ]
            }
if __name__ == "__main__":
    # Test
    skill = FinancialReportSkill()
    
    # Test US stock
    print("=== US Stock (AAPL) ===")
    print(skill.get_financial_metrics("AAPL"))
    print(skill.get_latest_report("AAPL"))
    
    # Test HK stock
    print("\n=== HK Stock (0700.HK) ===")
    print(skill.get_financial_metrics("0700.HK"))
    print(skill.get_latest_report("0700.HK"))
    
    # Test A-share
    print("\n=== A-Share (600036.SS) ===")
    print(skill.get_financial_metrics("600036.SS"))
    print(skill.get_latest_report("600036.SS"))
