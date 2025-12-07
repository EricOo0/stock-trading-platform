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
    predicate: str = Field(description="Relationship (e.g., analyzed, bought, related_to)")
    object: str = Field(description="Object entity name")

class ExtractedEvent(BaseModel):
    event_type: str = Field(description="Type of the event (e.g., MarketAnalysis, UserInstruction, Transaction)")
    summary: str = Field(description="Brief summary of the event")
    entities: List[Entity] = Field(description="List of entities involved")
    relations: List[Relation] = Field(description="List of relationships extracted")
    key_findings: Dict[str, Any] = Field(description="Key findings or data points as key-value pairs")

class EventExtractor:
    """
    事件抽取器
    负责从非结构化文本中抽取结构化事件 (IE)
    """
    
    def __init__(self):
        self.llm_client = LLMClient.get_instance()
        # 使用结构化输出能力 (Function Calling / JSON Mode)
        self.structured_llm = self.llm_client.get_llm().with_structured_output(ExtractedEvent)

    def extract(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本抽取事件
        """
        if not text:
            return None
            
        system_prompt = """Extract structured event information from the following text. 
Identify key entities (Stocks, People, Concepts), relationships, and key findings.
Ensure the extracted information is accurate and supported by the text.
"""
        
        try:
            # LangChain structured output 自动处理解析
            extracted_data: ExtractedEvent = self.structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=text)
            ])
            
            # 转换为 dict 用于后续处理 (兼容现有 schema)
            return {
                "event_type": extracted_data.event_type,
                "summary": extracted_data.summary,
                "entities": [e.name for e in extracted_data.entities],
                "relations": [(r.subject, r.predicate, r.object) for r in extracted_data.relations],
                "key_findings": extracted_data.key_findings
            }
        except Exception as e:
            logger.error(f"Event extraction failed: {e}")
            # Fallback for models that don't support tool calling well
            # 这里可以添加基于 JSON Prompting 的 fallback，暂略
            return None

# 单例
extractor = EventExtractor()
