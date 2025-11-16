# 行情数据工具 - 快速开始指南

## 概述

行情数据工具是一个基于Claude Skill的股票数据获取工具，支持A股、美股、港股的实时行情数据。本工具免费、易于使用，专为中文用户设计。

## 系统要求

- Python 3.11 或更高版本
- Claude AI 环境（作为Claude Skill调用）
- 网络连接（用于获取实时数据）

## 安装步骤

### 1. 克隆项目代码

```bash
git clone <project-repo>
cd <project-directory>
```

### 2. 创建Python虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

依赖包包括：
- `yfinance>=0.2.33` - Yahoo Finance数据获取
- `pandas>=1.5.0` - 数据处理
- `requests>=2.28.0` - HTTP请求
- `python-dotenv>=0.19.0` - 环境变量配置

### 4. 配置环境变量

创建 `.env` 文件（基于 `.env.example`）：

```env
# 行情数据工具配置
LOG_LEVEL=INFO
CACHE_TTL=300
RATE_LIMIT_A_SHARE=120
RATE_LIMIT_US=60
RATE_LIMIT_HK=60
```

## 基本使用方法

### 作为Claude Skill使用

在Claude环境中，直接调用技能：

```python
# 获取单只股票数据
result = "获取000001股票行情"

# 获取多只股票数据
result = "获取000001, AAPL, 00700的行情数据"

# 获取市场指数
result = "获取今日A股指数"
```

### 作为Python库使用

```python
from skills.market_data_tool.skill import MarketDataSkill

# 创建技能实例
skill = MarketDataSkill()

# 获取单只股票
data = skill.get_stock_quote("000001", market="A-share")
print(f"平安银行当前价格: {data['current_price']} 元")
print(f"涨跌幅: {data['change_percent']:.2f}%")

# 批量获取多只股票
symbols = ["000001", "600000", "300001"]
results = skill.get_batch_quotes(symbols)
for symbol, data in results.items():
    print(f"{symbol}: {data['name']} - {data['current_price']}")
```

## 支持的命令格式

### 1. 单只股票查询

文本格式：
```
获取000001股票
查询平安银行股价
AAPL股票价格是多少
```

### 2. 批量股票查询

文本格式：
```
获取000001,600000,300001的行情
查询茅台、腾讯、苹果的股票价格
比较AAPL,TSLA,MSFT的股价
```

### 3. 指数查询

文本格式：
```
获取上证指数
查询恒生指数
今日美股指数表现
```

### 4. 市场数据查询

文本格式：
```
获取A股市场数据
查询港股市场行情
今日美股市场概况
```

## 股票代码格式

### A股股票代码
- 6位数字
- 以000开头：深证主板
- 以600/601/603开头：上证主板
- 以002开头：深证中小板
- 以300开头：创业板

示例：
- 000001 (平安银行)
- 600000 (浦发银行)
- 300001 (特锐德)
- 002001 (新和成)

### 美股股票代码
- 1-5位字母
- 不区分大小写
- 常见股票：AAPL, MSFT, GOOGL, TSLA, AMZN

### 港股股票代码
- 5位数字
- 以0开头
- 示例：00700 (腾讯控股), 02318 (中国平安), 09988 (阿里巴巴)

## 返回数据格式

### 成功响应

```json
{
  "status": "success",
  "symbol": "000001",
  "data": {
    "symbol": "000001",
    "name": "平安银行",
    "current_price": 12.45,
    "change_percent": 2.38,
    "volume": 1234567,
    "timestamp": "2025-11-09 15:30:00",
    "market": "A-share",
    "currency": "CNY"
  },
  "timestamp": "2025-11-09 15:30:05"
}
```

### 错误响应

```json
{
  "status": "error",
  "symbol": "999999",
  "error_code": "INVALID_SYMBOL",
  "error_message": "股票代码 999999 格式不正确",
  "suggestion": "A股请输入6位数字代码，美股请输入1-5位字母代码，港股请输入5位数字代码"
}
```

## 使用限制

### 速率限制
- A股个股：每小时最多120次查询
- 美股个股：每小时最多60次查询
- 港股个股：每小时最多60次查询
- 批量查询：每次最多10只股票

### 数据延迟
- 数据延迟：约15-60分钟
- 非高频交易用途
- 适合日常投资决策

## 错误处理

### 常见错误代码

- `INVALID_SYMBOL`: 股票代码格式错误
- `SYMBOL_NOT_FOUND`: 股票代码不存在
- `RATE_LIMITED`: 请求频率超限
- `API_ERROR`: 数据源接口错误
- `SERVICE_UNAVAILABLE`: 服务暂不可用

### 错误处理建议

1. **格式错误**：检查股票代码格式是否正确
2. **频率超限**：等待1小时后再试，或查询其他股票
3. **服务不可用**：系统将自动尝试备用数据源
4. **代码不存在**：确认股票是否退市或代码更改

## 高级功能

### 1. 自定义数据源

```python
# 指定使用特定数据源
result = skill.get_quote("000001", provider="yahoo")
result = skill.get_quote("000001", provider="sina", primary=False)  # 备用数据源
```

### 2. 缓存控制

```python
# 忽略缓存获取最新数据
result = skill.get_quote("000001", ignore_cache=True)

# 设置自定义缓存时间
result = skill.get_quote("000001", cache_ttl=600)  # 缓存10分钟
```

### 3. 批量处理优化

```python
# 带错误处理的批量查询
results = skill.get_batch_quotes(symbols, include_errors=True)
for symbol, result in results.items():
    if result['status'] == 'error':
        print(f"{symbol} 查询失败: {result['error_message']}")
    else:
        print(f"{symbol}: {result['data']['current_price']}")
```

## 故障排除

### 1. 安装问题

问题：`pip install` 失败
解决：确保Python版本 >= 3.11，使用虚拟环境

### 2. 网络连接问题

问题：无法获取数据
解决：检查网络连接，确认可以访问外部API

### 3. 股票代码报错

问题：提示股票代码不存在
解决：确认代码格式正确，股票未退市

### 4. 性能问题

问题：响应时间过长
解决：检查网络质量，考虑使用缓存

## 测试使用

### 单元测试

```bash
# 运行所有测试
pytest

# 测试特定模块
pytest tests/test_skill.py

# 测试API集成
pytest tests/test_data_sources/ -v
```

### 集成测试示例

```python
import pytest
from skills.market_data_tool.skill import MarketDataSkill

def test_get_quote():
    skill = MarketDataSkill()
    result = skill.get_stock_quote("000001")

    assert result['status'] == 'success'
    assert result['symbol'] == '000001'
    assert 'current_price' in result['data']
    assert result['data']['market'] == 'A-share'
```

## 更新和维护

### 检查更新

定期检查依赖包更新：

```bash
pip list --outdated
pip install --upgrade yfinance pandas requests
```

### 数据源监控

系统将记录数据源使用情况：
- 主数据源成功率
- 备用数据源切换频率
- 响应时间统计

### 版本更新

遵循语义化版本控制：
- MAJOR: 重大功能变更
- MINOR: 新功能添加
- PATCH: Bug修复

## 技术支持

如遇到问题，请：

1. 检查本快速开始指南
2. 查看错误消息和建议
3. 检查GitHub Issues
4. 创建新的Issue并提供：
   - 错误代码和消息
   - 使用的股票代码
   - 复现步骤

## 免责声明

- 本工具仅供个人投资参考
- 数据可能存在延迟，不适用于高频交易
- 投资决策请结合多方信息，谨慎操作
- 过往表现不代表未来收益