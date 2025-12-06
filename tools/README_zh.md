
# 金融工具库 (Financial Tools Library)

本目录包含股票交易平台的金融工具集，提供市场数据、情感分析、网络搜索和文档解析功能。

## 目录结构

```
tools/
├── market/             # 市场数据
│   ├── sina.py         # 新浪财经 (A股/港股/美股)
│   ├── akshare.py      # AkShare (A股/宏观)
│   └── yahoo.py        # Yahoo Finance (全球)
├── search/             # 网页搜索
│   ├── tavily.py       # Tavily API
│   ├── serp.py         # SerpApi (Google)
│   └── duckduckgo.py   # DuckDuckGo (无需API)
├── reports/            # 财报工具
│   ├── finder.py       # 财报查找 (SEC/巨潮/港交所)
│   ├── content.py      # 内容提取 (HTML/PDF)
│   ├── analysis.py     # LLM 分析
│   └── pdf_parse.py    # PDF 解析 (LlamaParse/PyMuPDF)
├── analysis/           # 分析工具
│   └── finbert.py      # 情感分析 (FinBERT)
├── registry.py         # 中央注册表 (统一入口)
└── config.py           # 配置加载器
```

## 数据来源

*   **实时行情**: 新浪财经 (首选), Yahoo Finance (备选), AkShare (A股).
*   **财务数据**: AkShare (A股), Yahoo Finance (全球).
*   **新闻资讯**: 新浪财经 (爬虫), Tavily/Google/DuckDuckGo (搜索).
*   **公司财报**: SEC EDGAR (美股), 巨潮资讯 (A股), HKEX (港股).
*   **宏观数据**: AkShare (中国数据), Yahoo Finance (全球指标).

## 使用示例

```python
from tools.registry import Tools
# 或者
# from tools import Tools

# 初始化工具集
tools = Tools()

# 获取A股实时行# 情感分析
sentiment = tools.analyze_sentiment("分析师预测苹果公司将有强劲增长。")
print(sentiment)

# 获取财报元数据
report = tools.get_company_report("AAPL") # 返回 10-K/10-Q 元数据 (美股) 等
print(report)

# 解析 PDF
content = tools.parse_pdf("path/to/report.pdf")
print(content[:100])

# 获取宏观GDP数据
gdp = tools.get_macro_data("gdp")
```

## ⚠️ 注意事项
*   使用 `tavily_search.py` 需要配置环境变量 `TAVILY_API_KEY`.
*   `pdf_parse.py` 推荐配置 `LLAMA_CLOUD_API_KEY` 以获得最佳解析效果.
