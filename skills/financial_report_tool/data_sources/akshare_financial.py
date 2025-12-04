"""
AkShare财务数据源
专注于A股市场的财务指标获取
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any
from loguru import logger
from .base_financial import BaseFinancialSource

class AkShareFinancialSource(BaseFinancialSource):
    """AkShare财务数据源 - 专注A股"""
    
    def get_raw_data(self, symbol: str, years: int) -> pd.DataFrame:
        """
        获取AkShare财务指标数据
        
        Args:
            symbol: A股代码 (6位数字)
            years: 获取年数
            
        Returns:
            财务指标DataFrame
        """
        try:
            logger.info(f"Fetching AkShare financial data for {symbol}")
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # AkShare数据是倒序的(最老的在前),需要反转获取最新数据
            df = df.iloc[::-1].reset_index(drop=True)
            
            # 过滤最近N年数据 (每年4个季度)
            return df.head(years * 4 + 1)  # +1 是为了跳过可能的无效首行
            
        except Exception as e:
            logger.error(f"Error fetching AkShare data for {symbol}: {e}")
            return pd.DataFrame()
    
    def extract_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        从AkShare数据中提取5大类财务指标
        
        Args:
            df: AkShare财务指标DataFrame
            
        Returns:
            5大类指标字典
        """
        if df.empty or len(df) < 2:
            return self._empty_indicators()
        
        # 跳过第一行(日期为1900-01-01的无效数据),从第二行开始
        df = df.iloc[1:].reset_index(drop=True)
        
        try:
            return {
                "revenue": self._extract_revenue(df),
                "profit": self._extract_profit(df),
                "cashflow": self._extract_cashflow(df),
                "debt": self._extract_debt(df),
                "shareholder_return": self._extract_shareholder_return(df),
                "history": self._extract_history(df)
            }
        except Exception as e:
            logger.error(f"Error extracting indicators: {e}")
            return self._empty_indicators()
    
    def _extract_revenue(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        收入端指标
        1. 营业收入YoY
        2. 核心营收占比 (主营业务收入/总收入)
        3. 现金收入比
        """
        latest = df.iloc[0]
        
        # 营业收入YoY
        revenue_yoy = self._safe_get(latest, '主营业务收入增长率(%)', 0.0)
        
        # 核心营收占比
        core_revenue_ratio = self._safe_get(latest, '主营利润比重', 0.0)
        
        # 现金收入比 (需要计算)
        cash_to_revenue = self._calculate_cash_to_revenue(df)
        
        return {
            "revenue_yoy": round(revenue_yoy, 2),
            "core_revenue_ratio": round(core_revenue_ratio, 2),
            "cash_to_revenue": round(cash_to_revenue, 2)
        }
    
    def _extract_profit(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        利润端指标
        1. 扣非归母净利
        2. 经营毛利率
        3. 核心净利率
        """
        latest = df.iloc[0]
        
        # 扣非归母净利 (通过每股收益计算)
        non_recurring_eps = self._safe_get(latest, '扣除非经常性损益后的每股收益(元)', 0.0)
        
        # 经营毛利率
        gross_margin = self._safe_get(latest, '销售毛利率(%)', 0.0)
        
        # 核心净利率
        net_margin = self._safe_get(latest, '销售净利率(%)', 0.0)
        
        return {
            "non_recurring_eps": round(non_recurring_eps, 4),
            "gross_margin": round(gross_margin, 2),
            "net_margin": round(net_margin, 2)
        }
    
    def _extract_cashflow(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        现金流指标
        1. 经营现金流净额/归母净利
        2. 自由现金流FCF
        """
        latest = df.iloc[0]
        
        # 经营现金流/归母净利
        ocf_per_share = self._safe_get(latest, '每股经营性现金流(元)', 0.0)
        eps = self._safe_get(latest, '每股收益_调整后(元)', 1.0)
        ocf_to_net_profit = (ocf_per_share / eps) if eps != 0 else 0.0
        
        # 自由现金流 (AkShare不直接提供,暂时为None)
        free_cash_flow = None
        
        return {
            "ocf_to_net_profit": round(ocf_to_net_profit, 2),
            "free_cash_flow": free_cash_flow
        }
    
    def _extract_debt(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        负债端指标
        1. 资产负债率
        2. 流动比率
        """
        latest = df.iloc[0]
        
        asset_liability_ratio = self._safe_get(latest, '资产负债率(%)', 0.0)
        current_ratio = self._safe_get(latest, '流动比率', 0.0)
        
        return {
            "asset_liability_ratio": round(asset_liability_ratio, 2),
            "current_ratio": round(current_ratio, 2)
        }
    
    def _extract_shareholder_return(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        股东回报指标
        1. 股息率
        2. ROE (净资产收益率)
        """
        latest = df.iloc[0]
        
        dividend_yield = self._safe_get(latest, '股息发放率(%)', 0.0)
        roe = self._safe_get(latest, '净资产收益率(%)', 0.0)
        
        return {
            "dividend_yield": round(dividend_yield, 2),
            "roe": round(roe, 2)
        }
    
    def _extract_history(self, df: pd.DataFrame) -> list:
        """提取历史数据"""
        history = []
        for _, row in df.iterrows():
            history.append({
                "date": str(row.get('日期', '')),
                "roe": round(self._safe_get(row, '净资产收益率(%)', 0.0), 2),
                "gross_margin": round(self._safe_get(row, '销售毛利率(%)', 0.0), 2),
                "net_margin": round(self._safe_get(row, '销售净利率(%)', 0.0), 2),
                "asset_liability_ratio": round(self._safe_get(row, '资产负债率(%)', 0.0), 2)
            })
        return history
    
    def _calculate_cash_to_revenue(self, df: pd.DataFrame) -> float:
        """
        计算现金收入比
        使用每股经营性现金流作为近似
        """
        if df.empty:
            return 0.0
        
        latest = df.iloc[0]
        ocf_per_share = self._safe_get(latest, '每股经营性现金流(元)', 0.0)
        
        # 简化计算: 如果OCF为正,返回1.0以上,否则返回比例
        # 实际应该用 (销售商品收到的现金 / 营业收入)
        return 1.0 if ocf_per_share > 0 else 0.0
    
    @staticmethod
    def _safe_get(row: pd.Series, key: str, default: float = 0.0) -> float:
        """安全获取数值,处理NaN"""
        value = row.get(key, default)
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _empty_indicators() -> Dict[str, Any]:
        """返回空指标结构"""
        return {
            "revenue": {},
            "profit": {},
            "cashflow": {},
            "debt": {},
            "shareholder_return": {},
            "history": []
        }
