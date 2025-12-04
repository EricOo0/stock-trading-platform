"""
财务数据源基类
定义统一的数据获取接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseFinancialSource(ABC):
    """财务数据源基类"""
    
    @abstractmethod
    def get_raw_data(self, symbol: str, years: int) -> Any:
        """
        获取原始数据
        
        Args:
            symbol: 股票代码
            years: 获取年数
            
        Returns:
            原始数据 (格式由子类定义)
        """
        pass
    
    @abstractmethod
    def extract_indicators(self, raw_data: Any) -> Dict[str, Any]:
        """
        从原始数据中提取财务指标
        
        Args:
            raw_data: 原始数据
            
        Returns:
            标准化的财务指标字典,包含5大类:
            - revenue: 收入端指标
            - profit: 利润端指标  
            - cashflow: 现金流指标
            - debt: 负债端指标
            - shareholder_return: 股东回报指标
        """
        pass
    
    def get_financial_indicators(self, symbol: str, years: int = 3) -> Dict[str, Any]:
        """
        统一接口: 获取财务指标
        
        Args:
            symbol: 股票代码
            years: 获取年数 (默认3年)
            
        Returns:
            财务指标字典
        """
        raw_data = self.get_raw_data(symbol, years)
        return self.extract_indicators(raw_data)
