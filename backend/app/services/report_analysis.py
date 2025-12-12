
import logging
import re
import os
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from backend.infrastructure.config.loader import config

logger = logging.getLogger(__name__)

class ReportAnalysisTool:
    """
    Analyzes financial reports using an LLM.
    Generates markdown reports with citations pointing to original content anchors.
    """

    def __init__(self):
        # Load LLM settings from config or env
        api_key = config.get_api_key("siliconflow") or config.get_api_key("openai") or os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # Default to SiliconFlow/DeepSeek if available, otherwise check others
        if not api_key:
             logger.warning("No LLM API Key found (SiliconFlow/OpenAI). Analysis may fail.")
        
        # Determine base URL and Model
        # TODO: Make these configurable via tools/config.py explicitly
        self.api_base = "https://api.siliconflow.cn/v1" if config.get_api_key("siliconflow") or os.getenv("SILICONFLOW_API_KEY") else "https://api.openai.com/v1"
        self.model = "deepseek-ai/DeepSeek-V3.1-Terminus" if "siliconflow" in self.api_base else "gpt-4o"
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0,
            base_url=self.api_base,
            api_key=api_key or "dummy" # LangChain requires a key even if invalid
        )

    def analyze_content(
        self, 
        content: str, 
        symbol: str, 
        market: str, 
        report_info: Dict[str, Any],
        pdf_url: str,
        anchor_map: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyzes the financial report content using LLM.
        """
        try:
            if not content:
                return {"error": "Report content is empty"}

            # Truncate content
            truncated_content = content[:300000]
            
            prompt = f"""
You are a professional financial analyst. Analyze the following financial report content for {symbol} ({market}).
The content may be a full text report (e.g., 10-K/Annual Report) or structured financial data tables.
The provided content is extensive. Please analyze ALL of it to extract key insights.

Content (Truncated to {len(truncated_content)} chars):
{truncated_content}

Please provide a comprehensive analysis in Markdown format, strictly following this structure:

## 核心财务指标
- **收入**: [Value] (同比 [Growth]%, 环比 [Growth]%)
- **净利润**: [Value] (净利率 [Margin]%)
- **现金流**: [Description]
- **每股收益 (EPS)**: [Value]

## 关键业务亮点
- [Point 1]
- [Point 2]
(Extract business highlights or infer trends.)

## 管理层讨论与分析 (MD&A) 要点 / 财务健康诊断
- **未来展望**: [Key points]
- **风险与机遇**: [Key points]

## 市场对比与评价
- [Comparison]
- [Overall sentiment]

**Note**: 
- **IMPORTANT**: If the input content has anchors like `[html_123]` or `[pdf_1_2]`, you MUST use them for citations.
- Format: `[ID]` (e.g., `[html_5]`, `[pdf_1_2]`).
- Do NOT include links inside citations.
- List multiple citations individually: `[html_1] [html_2]`.
- Do NOT invent anchor IDs.
"""
            logger.info(f"Sending analysis request to LLM for {symbol}...")
            messages = [
                SystemMessage(content="You are a helpful and professional financial analyst assistant."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            report_markdown = response.content
            
            # Sanitization
            report_markdown = self._sanitize_markdown(report_markdown)
            
            # Extract citations
            citations = self._extract_citations(report_markdown, anchor_map)
            
            final_pdf_url = pdf_url or report_info.get("download_url", "")
            
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
            return {"error": str(e)}

    def _sanitize_markdown(self, text: str) -> str:
        if text.startswith("```markdown"): return text[11:-3].strip() if text.endswith("```") else text[11:].strip()
        if text.startswith("```"): return text[3:-3].strip() if text.endswith("```") else text[3:].strip()
        return text.strip()

    def _extract_citations(self, text: str, anchor_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        used_anchors = re.findall(r'\[(?:锚点:\s*)?((?:pdf|html)_[0-9_-]+)\]', text)
        citations = []
        seen_ids = set()
        
        for anchor_id in used_anchors:
            if anchor_id in anchor_map and anchor_id not in seen_ids:
                info = anchor_map[anchor_id]
                citations.append({
                    "id": anchor_id,
                    "content": info.get("content", ""),
                    "page_num": info.get("page", 1),
                    "rect": info.get("rect"),
                    "type": info.get("type", "pdf")
                })
                seen_ids.add(anchor_id)
        return citations
