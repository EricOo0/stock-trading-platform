from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger
import re

def analyze_report_content(
    llm: Any, 
    content: str, 
    symbol: str, 
    market: str, 
    report_info: Dict[str, Any],
    pdf_url: str,
    anchor_map: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyzes the financial report using LLM.
    Returns a markdown report.
    """
    try:
        if not content:
            return {
                "status": "error",
                "message": "Report content is empty",
                "symbol": symbol
            }
            
        # Truncate content to fit context window if necessary
        truncated_content = content[:300000]
        
        prompt = f"""
You are a professional financial analyst. Analyze the following financial report content for {symbol} ({market}).
The content may be a full text report (e.g., 10-K/Annual Report) or structured financial data tables (Income Statement, Balance Sheet, etc.).
The provided content is extensive. Please analyze ALL of it to extract key insights, especially from the MD&A and Financial Statements sections.

Content (Truncated to {len(truncated_content)} chars):
{truncated_content}

Please provide a comprehensive analysis in Markdown format, strictly following this structure:

## 核心财务指标
- **收入**: [Value] (同比 [Growth]%, 环比 [Growth]%) - Calculate from tables if necessary.
- **净利润**: [Value] (净利率 [Margin]%)
- **现金流**: [Description of cash flow status]
- **每股收益 (EPS)**: [Value]

## 关键业务亮点
- [Point 1]
- [Point 2]
- [Point 3]
(If full text is available, extract specific business highlights. If only data tables are available, infer trends from the numbers.)

## 管理层讨论与分析 (MD&A) 要点 / 财务健康诊断
- **未来展望**: [Key points] (If available in text, otherwise infer from trends)
- **风险与机遇**: [Key points] (If available in text, otherwise infer from financial stability)

## 市场对比与评价
- [Comparison with expectations or peers]
- [Overall sentiment/rating]

**Note**: 
- **IMPORTANT**: If the input content has anchors like `[html_123]`, you MUST use `[html_123]` format for citations.
- **IMPORTANT**: If the input content has anchors like `[pdf_1_2]`, you MUST use `[pdf_1_2]` format for citations.
- **DO NOT MIX TYPES**: If the content is HTML (has `html_` anchors), do NOT hallucinate `pdf_` anchors.
- Format: `[ID]` (e.g., `[html_5]` or `[pdf_1_2]`).
- **STRICTLY FORBIDDEN**: Do NOT include anchor links or URLs inside the citation. Use ONLY `[html_123]`.
- **STRICTLY FORBIDDEN**: Do NOT generate `[html_123](#anchor-html_123)`.
- **STRICTLY FORBIDDEN**: Do NOT wrap citations in parentheses. Use `[html_123]` directly, NOT `([html_123])`.
- **STRICTLY FORBIDDEN**: Do NOT use ranges like `[html_34-37]` or `[pdf_1_5-7]`.
- **STRICTLY FORBIDDEN**: Do NOT use combined formats like `[html_34, 35]`.
- **REQUIRED**: If multiple anchors apply, you MUST list them individually with full tags, e.g., `[html_34] [html_35] [html_36] [html_37]` or `[pdf_1_5] [pdf_1_6]`.
- Do NOT invent anchor IDs that are not present in the source text.
- If specific text data is not available, derive insights from the financial tables provided.
- If a specific metric cannot be calculated, state "数据不足" or "Not available".
- Use professional financial terminology.
"""

        logger.info(f"Sending analysis request to LLM for {symbol}...")
        messages = [
            SystemMessage(content="You are a helpful and professional financial analyst assistant."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        report_markdown = response.content
        
        # Strip markdown code blocks if present
        if report_markdown.startswith("```markdown"):
            report_markdown = report_markdown[11:]
        elif report_markdown.startswith("```"):
            report_markdown = report_markdown[3:]
        
        if report_markdown.endswith("```"):
            report_markdown = report_markdown[:-3]
            
        report_markdown = report_markdown.strip()
        
        # Use the pdf_url from params
        final_pdf_url = pdf_url or report_info.get("download_url", "")
        
        citations = [] 
        
        # Parse the report to find used anchors and populate citations for the UI list
        # Match [pdf_1_2], [html_5], [锚点: pdf_1_2], support hyphens
        used_anchors = re.findall(r'\[(?:锚点:\s*)?((?:pdf|html)_[0-9_-]+)\]', report_markdown)
        
        seen_ids = set()
        for anchor_id in used_anchors:
            if anchor_id in anchor_map and anchor_id not in seen_ids:
                info = anchor_map[anchor_id]
                citations.append({
                    "id": anchor_id,
                    "content": info.get("content", ""),
                    "page_num": info.get("page", 1), # For PDF
                    "rect": info.get("rect"),
                    "type": info.get("type", "pdf")
                })
                seen_ids.add(anchor_id)

        return {
            "status": "success",
            "symbol": symbol,
            "market": market,
            "report": report_markdown,
            "report_date": report_info.get("filing_date", "Unknown"),
            "citations": citations,
            "pdf_url": final_pdf_url,
            "anchor_map": anchor_map
        }

    except Exception as e:
        logger.error(f"Error analyzing report for {symbol}: {e}")
        return {"status": "error", "message": str(e), "symbol": symbol}
