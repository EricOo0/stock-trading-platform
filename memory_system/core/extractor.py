from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from llm.client import LLMClient
from config import settings
from utils.logger import logger
import json


# 定义输出结构 (Pydantic v1 for LangChain compatibility)
class Entity(BaseModel):
    name: str = Field(description="Name of the entity")
    type: str = Field(description="Type of the entity (e.g., Person, Stock, Concept)")


class Relation(BaseModel):
    subject: str = Field(description="Subject entity name")
    predicate: str = Field(
        description="Relationship (e.g., analyzed, bought, related_to)"
    )
    object: str = Field(description="Object entity name")


class ExtractedEvent(BaseModel):
    event_type: str = Field(
        description="Type of the event (e.g., MarketAnalysis, UserInstruction, Transaction)"
    )
    summary: str = Field(description="Brief summary of the event")
    entities: List[Entity] = Field(description="List of entities involved")
    relations: List[Relation] = Field(description="List of relationships extracted")
    key_findings: Dict[str, Any] = Field(
        description="Key findings or data points as key-value pairs"
    )


class InvestmentInsight(BaseModel):
    """投研见解结构化模型"""

    symbol: str = Field(description="股票或资产代码，如 NVDA, AAPL")
    viewpoint: str = Field(description="投资观点，必须是 Bullish, Bearish, 或 Neutral")
    core_logic: List[str] = Field(description="支撑该观点的核心逻辑节点")
    key_metrics: Dict[str, Any] = Field(description="关键财务或技术指标")
    confidence: float = Field(description="对该判断的信心指数 (0.0-1.0)")
    valid_until: Optional[str] = Field(description="该判断的预期有效期或触发失效的条件")


class UserPersona(BaseModel):
    """用户画像结构化模型"""
    risk_preference: str = Field(description="风险偏好 (e.g., Aggressive, Conservative, Balanced)")
    investment_style: List[str] = Field(description="投资风格 (e.g., Value, Growth, Technical, Quant)")
    interested_sectors: List[str] = Field(description="感兴趣的行业或领域")
    analysis_habits: List[str] = Field(description="关注的分析维度 (e.g., Macro, CashFlow, Sentiment)")
    observed_traits: List[str] = Field(description="从对话中观察到的用户性格或习惯")


class EventExtractor:
    """
    事件抽取器
    负责从非结构化文本中抽取结构化事件 (IE)
    """

    def __init__(self):
        self.llm_client = LLMClient.get_instance()
        # 通用事件提取
        self.structured_llm = self.llm_client.get_llm().with_structured_output(
            ExtractedEvent
        )
        # 投研专用提取
        self.investment_llm = self.llm_client.get_llm().with_structured_output(
            InvestmentInsight
        )
        # 用户画像提取
        self.persona_llm = self.llm_client.get_llm().with_structured_output(
            UserPersona
        )

    def extract(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本抽取通用事件
        """
        if not text:
            return None

        system_prompt = """Extract structured event information from the following text. 
Identify key entities (Stocks, People, Concepts), relationships, and key findings.
Ensure the extracted information is accurate and supported by the text.
"""

        try:
            extracted_data: ExtractedEvent = self.structured_llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=text)]
            )

            return {
                "event_type": extracted_data.event_type,
                "summary": extracted_data.summary,
                "entities": [e.name for e in extracted_data.entities],
                "relations": [
                    (r.subject, r.predicate, r.object) for r in extracted_data.relations
                ],
                "key_findings": extracted_data.key_findings,
            }
        except Exception as e:
            logger.error(f"Event extraction failed: {e}")
            return None

    def extract_investment_insight(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从投研报告或对话中抽取投资见解
        """
        if not text:
            return None

        system_prompt = """你是一名资深金融分析师。请从提供的研究报告或对话记录中提取结构化的投资见解。
注意：
1. viewpoint 必须是 Bullish (看多), Bearish (看空), 或 Neutral (中性)。
2. core_logic 应包含最核心的支撑论点。
3. 如果文中没有明确的标的，请勿强行提取。
"""
        try:
            insight: InvestmentInsight = self.investment_llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=text)]
            )
            return insight.dict()
        except Exception as e:
            logger.error(f"Investment insight extraction failed: {e}")
            return None

    def extract_user_persona(self, conversation_text: str) -> Optional[Dict[str, Any]]:
        """
        从多轮对话语料中提取或更新用户画像信息
        """
        if not conversation_text:
            return None

        system_prompt = """你是一名心理学家和资深理财顾问。请分析提供的对话记录，刻画出用户的投资人画像。
注意：
1. 风险偏好：根据用户对回撤的忍受度、对高收益的追求等判断。
2. 投资风格：判断用户是价值投资、成长投资、还是短线投机等。
3. 分析习惯：用户是更看重基本面、技术面、还是宏观消息？
4. 只提取证据充分的信息，如果对话不足以支撑某项判断，请保留为空或默认。
"""
        try:
            persona: UserPersona = self.persona_llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=conversation_text)]
            )
            return persona.dict()
        except Exception as e:
            logger.error(f"User persona extraction failed: {e}")
            return None


# 单例
extractor = EventExtractor()
