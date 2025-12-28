from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
import json
from pathlib import Path
from config import settings
from storage.vector_store import VectorStore
from utils.logger import logger
from utils.embeddings import embedding_service


class SemanticMemory:
    """长期记忆管理器 (Semantic Memory)"""

    def __init__(self, user_id: str, agent_id: str):
        self.user_id = user_id
        self.agent_id = agent_id
        # 持久化文件路径
        self.file_path = settings.DATA_DIR / f"semantic_{user_id}_{agent_id}.json"
        
        # 长期记忆使用独立的向量集合，增加 user_id 隔离
        self.experience_store = VectorStore(
            collection_name=f"semantic_exp_{user_id}_{agent_id}"
        )
        self.core_principles: List[Dict] = []
        # 用户画像
        self.user_persona: Dict[str, Any] = {
            "risk_preference": "Balanced",
            "investment_style": [],
            "interested_sectors": [],
            "analysis_habits": [],
            "observed_traits": [],
            "last_updated": None
        }
        
        # 初始化时加载磁盘数据
        self._load_from_disk()

    def _save_to_disk(self) -> None:
        """持久化画像与原则到磁盘"""
        try:
            data = {
                "user_persona": self.user_persona,
                "core_principles": self.core_principles
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved semantic memory to {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to save semantic memory: {e}")

    def _load_from_disk(self) -> None:
        """从磁盘加载画像与原则"""
        if not self.file_path.exists():
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.user_persona = data.get("user_persona", self.user_persona)
                self.core_principles = data.get("core_principles", [])
            logger.info(f"Loaded semantic memory from {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to load semantic memory: {e}")

    def update_persona(self, new_traits: Dict[str, Any]) -> None:
        """增量更新用户画像"""
        if not new_traits:
            return

        # 1. 简单合并逻辑 (后续可升级为 LLM 冲突消解)
        if new_traits.get("risk_preference"):
            self.user_persona["risk_preference"] = new_traits["risk_preference"]

        # 列表类属性进行去重合并
        for key in ["investment_style", "interested_sectors", "analysis_habits", "observed_traits"]:
            if new_traits.get(key):
                existing = set(self.user_persona.get(key, []))
                incoming = set(new_traits[key])
                self.user_persona[key] = list(existing.union(incoming))

        self.user_persona["last_updated"] = datetime.now().isoformat()
        logger.info(f"Updated user persona for {self.user_id}")
        self._save_to_disk()

    def get_persona_summary(self) -> str:
        """获取画像的文本总结，用于注入 System Prompt"""
        p = self.user_persona
        if not p.get("last_updated"):
            return "No persona data available yet."

        summary = f"User Persona (Last Updated: {p['last_updated']}):\n"
        summary += f"- Risk Preference: {p['risk_preference']}\n"
        summary += f"- Investment Style: {', '.join(p['investment_style'])}\n"
        summary += f"- Interested Sectors: {', '.join(p['interested_sectors'])}\n"
        summary += f"- Analysis Habits: {', '.join(p['analysis_habits'])}\n"
        summary += f"- Observed Traits: {', '.join(p['observed_traits'])}"
        return summary

    def add_core_principle(self, content: str, importance: float = 1.0) -> None:
        """添加核心原则 (内存存储，少量)"""
        self.core_principles.append(
            {
                "user_id": self.user_id,
                "agent_id": self.agent_id,
                "content": content,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
            }
        )
        # 排序保持高优先级的在前
        self.core_principles.sort(key=lambda x: x["importance"], reverse=True)

        # 限制数量
        if len(self.core_principles) > settings.CORE_PRINCIPLES_LIMIT:
            self.core_principles = self.core_principles[
                : settings.CORE_PRINCIPLES_LIMIT
            ]
        self._save_to_disk()

    def add_experience(
        self, content: str, category: str, importance: float = 0.5
    ) -> str:
        """添加经验法则 (向量存储)"""
        memory_id = str(uuid.uuid4())

        metadata = {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "importance": importance,
            "type": "semantic",
        }

        self.experience_store.add(
            documents=[content], metadatas=[metadata], ids=[memory_id]
        )

        logger.debug(
            f"Added SemanticMemory experience (ID: {memory_id}, User: {self.user_id})"
        )
        return memory_id

    def get_core_principles(self) -> str:
        """获取格式化的核心原则"""
        return "\n".join([f"- {p['content']}" for p in self.core_principles])

    def retrieve_relevant_experiences(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索相关经验，返回结构化数据"""
        results = self.experience_store.query(query_text=query, n_results=top_k)

        experiences = []
        if (
            results["documents"]
            and len(results["documents"]) > 0
            and len(results["documents"][0]) > 0
        ):
            for i, doc in enumerate(results["documents"][0]):
                metadata = (
                    results["metadatas"][0][i]
                    if results.get("metadatas") and len(results["metadatas"][0]) > i
                    else {}
                )
                experiences.append(
                    {
                        "content": doc,
                        "importance": metadata.get("importance", 0.5),
                        "category": metadata.get("category", "general"),
                    }
                )

        return experiences
