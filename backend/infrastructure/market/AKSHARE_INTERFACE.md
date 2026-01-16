# AkShare 接口分类文档 (重构参考)

该文档整理了重构 `AkShareTool` 所需的核心接口，涵盖了 8 大功能分类，旨在为个人理财助手提供全方位的实时与历史数据支持。

## 1. 个股数据 (Individual Stock Data)
用于获取各市场个股的实时快照及基本信息。
- **A股实时快照**: `stock_zh_a_spot_em` (支持全市场，带 PE/PB/市值)
- **A股分时行情**: `stock_zh_a_hist_min_em` (支持 1, 5, 15, 30, 60 分钟)
- **港股实时快照**: `stock_hk_spot_em`
- **美股实时快照**: `stock_us_spot_em`
- **个股基本信息**: `stock_individual_info_em` (上市日期、总市值、流通市值、行业)

## 2. ETF 数据 (ETF Data)
针对基金/ETF 的专项实时数据。
- **ETF 实时行情**: `fund_etf_spot_em`
- **ETF 历史行情**: `fund_etf_hist_em`
- **ETF 分时数据**: `fund_etf_hist_min_em`

## 3. 板块数据 (Sector & Concept Data)
用于板块分析、热度排名及成分股映射（背离检测核心数据）。
- **行业资金流排名**: `stock_fund_flow_industry` (支持 即时/3日/5日/10日 净流入排名)
- **概念资金流排名**: `stock_fund_flow_concept`
- **行业成份股**: `stock_board_industry_cons_em`
- **概念成份股**: `stock_board_concept_cons_em`
- **板块历史行情**: `stock_board_industry_hist_em`

## 4. 资金流向 (Fund Flow)
多维度的资金监控指标。
- **个股资金流历史**: `stock_individual_fund_flow`
- **北向资金流**: `stock_hsgt_north_net_flow_in_em` (沪深港通-北向)
- **南向资金流**: `stock_hsgt_south_net_flow_in_em` (沪深港通-南向)
- **两融数据明细**: `stock_margin_detail_szkz_em` (市场整体融资融券情绪)

## 5. 公司基本面 (Fundamentals)
财报、估值指标及股东回报。
- **财务指标分析**: `stock_financial_analysis_indicator` (ROE, 毛利, 净利等历年数据)
- **财务报表摘要**: `stock_financial_abstract` (最新财报核心数)
- **分红送配**: `stock_fhps_em` (历年分红方案)

## 6. 历史行情 (Historical Data)
全市场的日/周/月 K 线序列。
- **A股历史 K 线**: `stock_zh_a_hist` (支持前复权 qfq, 后复权 hfq)
- **港股历史 K 线**: `stock_hk_hist`
- **美股历史 K 线**: `stock_us_hist`

## 7. 宏观经济 (Macro Economics)
主要关注中国宏观指标（配合 Fred 补充全球数据）。
- **中国 GDP**: `macro_china_gdp`
- **中国 CPI**: `macro_china_cpi`
- **中国 PMI**: `macro_china_pmi`
- **货币供应量 (M2)**: `macro_china_money_supply`
- **贷款市场报价利率 (LPR)**: `macro_china_lpr`

## 8. 经济日历与新闻 (Calendar & News)
日内实战的新闻与事件触发。
- **全球经济日历**: `news_economic_baidu` (百度财经提供)
- **全球财经新闻**: `stock_info_global_ths` (同花顺全球快讯)
- **新闻联播摘要**: `news_cctv` (关键政策风向标)
