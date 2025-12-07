from typing import Dict, List, Optional, Any
from datetime import datetime
from .working_memory import WorkingMemory
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .compressor import MemoryCompressor
from .extractor import EventExtractor
from .cluster import ConceptCluster
from config import settings
from utils.logger import logger
from utils.tokenizer import tokenizer

class MemoryManager:
    """
    记忆系统核心管理器
    负责协调三层记忆系统，为每个 Agent 维护独立的记忆实例
    """
    
    _instances: Dict[str, 'MemoryManager'] = {}

    def __init__(self):
        # 按 agent_id 存储记忆实例
        self.working_memories: Dict[str, WorkingMemory] = {}
        self.episodic_memories: Dict[str, EpisodicMemory] = {}
        self.semantic_memories: Dict[str, SemanticMemory] = {}
        logger.info("MemoryManager initialized")

    @classmethod
    def get_instance(cls) -> 'MemoryManager':
        """单例模式获取管理器"""
        if "default" not in cls._instances:
            cls._instances["default"] = cls()
        return cls._instances["default"]

    def _get_working_memory(self, agent_id: str) -> WorkingMemory:
        if agent_id not in self.working_memories:
            wm = WorkingMemory(agent_id)
            # 设置压缩回调
            wm.set_compression_callback(lambda items: self._handle_compression(agent_id, items))
            self.working_memories[agent_id] = wm
        return self.working_memories[agent_id]

    def _get_episodic_memory(self, agent_id: str) -> EpisodicMemory:
        if agent_id not in self.episodic_memories:
            self.episodic_memories[agent_id] = EpisodicMemory(agent_id)
        return self.episodic_memories[agent_id]

    def _get_semantic_memory(self, agent_id: str) -> SemanticMemory:
        if agent_id not in self.semantic_memories:
            self.semantic_memories[agent_id] = SemanticMemory(agent_id)
        return self.semantic_memories[agent_id]

    def add_memory(self, agent_id: str, content: Any, role: str = "user", memory_type: str = "conversation", metadata: Dict = None) -> Dict[str, Any]:
        """
        添加记忆 - 简化版统一接口
        
        Args:
            agent_id: Agent ID
            content: 记忆内容 (通常是字符串)
            role: 角色 (user/agent/system)
            memory_type: 类型 (默认 conversation, 系统自动处理流转)
            metadata: 元数据
        """
        if metadata is None:
            metadata = {}
            
        stored_locations = []
        memory_id = None
        
        # 1. 默认全部进入 Working Memory (近期记忆)
        if memory_type == "conversation":
            wm = self._get_working_memory(agent_id)
            wm.add({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            })
            stored_locations.append("working_memory")
            
            # 2. 检查是否需要触发 Episodic -> Semantic 的提升 (维护检查)
            # 这里的触发频率可以降低，例如 random 1% 或者计数器
            # 简化起见，每次添加都 check 一下 (内部有计数器/阈值判断)
            self._check_and_promote_to_semantic(agent_id)
            
        # 3. 兼容旧的 'event' 类型 (直接存入 Episodic)，但建议通过 pipeline 自动产生
        # 这里保留是为了测试方便，或者极少数确定的关键事件
        elif memory_type == "event":
            # 复用之前的自动提取逻辑
            if isinstance(content, str):
                extracted_data = extractor.extract(content)
                if extracted_data:
                    content_data = {
                        "summary": extracted_data["summary"],
                        "key_findings": extracted_data["key_findings"]
                    }
                    entities = extracted_data["entities"]
                    relations = extracted_data["relations"]
                    if "event_type" not in metadata:
                        metadata["event_type"] = extracted_data.get("event_type", "unknown_event")
                else:
                    content_data = {"raw_content": content}
                    entities = []
                    relations = []
            else:
                 # 结构化数据
                 if isinstance(content, dict):
                     content_data = content.get("content", content)
                     entities = content.get("entities", [])
                     relations = content.get("relations", [])
                 else:
                     content_data = str(content)
                     entities = []
                     relations = []

            em = self._get_episodic_memory(agent_id)
            memory_id = em.add_event(
                event_type=metadata.get("event_type", "manual_event"),
                content=content_data,
                entities=entities,
                relations=relations,
                importance=metadata.get("importance", 0.5)
            )
            stored_locations.append("episodic_memory")
            # 同样检查提升
            self._check_and_promote_to_semantic(agent_id)

        return {
            "status": "success",
            "memory_id": memory_id or "wm_latest",
            "stored_in": stored_locations
        }

    def get_context(self, agent_id: str, query: str, session_id: str = None) -> Dict:
        """
        获取完整上下文
        """
        wm = self._get_working_memory(agent_id)
        em = self._get_episodic_memory(agent_id)
        sm = self._get_semantic_memory(agent_id)
        
        # 1. 核心原则
        core_principles = sm.get_core_principles()
        core_tokens = tokenizer.count_tokens(core_principles)
        
        # 2. 近期记忆 (完整)
        working_context = wm.get_details() # 返回结构化数据供前端处理
        # 计算 working memory tokens (直接使用 wm 中维护的总数或重新计算)
        # 这里使用 wm.total_tokens() 更准确，因为它维护了内部 count
        working_tokens = wm.total_tokens()
        
        # 3. 中期记忆 (相关性检索)
        episodic_context = em.retrieve(query, top_k=5)
        # 计算 episodic tokens
        episodic_str = str(episodic_context) # 简单估算，或者遍历计算
        episodic_tokens = tokenizer.count_tokens(episodic_str)
        
        # 4. 长期记忆 (经验检索)
        semantic_context = sm.retrieve_relevant_experiences(query, top_k=3)
        semantic_tokens = tokenizer.count_tokens(semantic_context)
        
        total_tokens = core_tokens + working_tokens + episodic_tokens + semantic_tokens
        
        return {
            "core_principles": core_principles,
            "working_memory": working_context,
            "episodic_memory": episodic_context,
            "semantic_memory": semantic_context,
            "token_usage": {
                "core_principles": core_tokens,
                "working_memory": working_tokens,
                "episodic_memory": episodic_tokens,
                "semantic_memory": semantic_tokens,
                "total": total_tokens
            }
        }

    def _handle_compression(self, agent_id: str, items: List[Dict]):
        """
        处理近期记忆压缩 (Working -> Episodic)
        Pipeline: Summary + Event Extraction
        """
        try:
            logger.info(f"Starting compression pipeline for agent {agent_id} ({len(items)} items)")
            em = self._get_episodic_memory(agent_id)

            # 1. 生成对话摘要 (Conversation Summary)
            summary = compressor.summarize_conversation(items)
            if summary:
                em.add_event(
                    event_type="conversation_summary",
                    content={"summary": summary, "source_items_count": len(items)},
                    importance=0.4
                )
            
            # 2. 提取结构化事件 (Event Extraction)
            # 将多条消息合并为文本进行提取 (或逐条提取，视 contexts 长度而定)
            # 这里选择合并后提取，以捕捉上下文
            combined_text = "\n".join([f"{item['role']}: {item['content']}" for item in items])
            
            event_data = extractor.extract(combined_text)
            if event_data:
                # 只有当提取出有意义的信息时才保存
                if event_data.get("entities") or event_data.get("key_findings"):
                     em.add_event(
                        event_type=event_data["event_type"],
                        content={
                            "summary": event_data["summary"],
                            "key_findings": event_data["key_findings"]
                        },
                        entities=event_data["entities"],
                        relations=event_data["relations"],
                        importance=0.7 # 自动提取的事件重要性适中
                    )
            
            logger.info(f"Compression pipeline completed for {agent_id}")

        except Exception as e:
            logger.error(f"Compression handler failed: {e}")

    def _check_and_promote_to_semantic(self, agent_id: str):
        """
        检查并提升到长期记忆 (Episodic -> Semantic)
        简单策略：如果有 10 条以上的新 Episodic Memory，触发聚类
        """
        # 注意：这里需要一个计数器或者状态来避免每次都触发
        # 简化实现：使用 random 采样模拟 "每隔一段时间"
        import random
        if random.random() < 0.05: # 5% 的概率触发维护
             logger.info(f"Triggering periodic Semantic promotion for {agent_id}")
             # 异步或同步？为了不阻塞 add_memory，最好是异步
             # 但这里是在 manager 内部，无法直接用 background tasks
             # 实际生产中应抛出事件或放到任务队列
             # 这里暂且同步执行 (因为是 demo/mvp)
             self.run_clustering(agent_id)

    def extract_and_save_event(self, agent_id: str, text: str) -> Optional[str]:
        """主动提取事件并保存"""
        try:
            event_data = extractor.extract(text)
            if event_data:
                em = self._get_episodic_memory(agent_id)
                memory_id = em.add_event(
                    event_type=event_data["event_type"],
                    content={
                        "summary": event_data["summary"],
                        "key_findings": event_data["key_findings"]
                    },
                    entities=event_data["entities"],
                    relations=event_data["relations"],
                    importance=0.8 # 提取出的事件通常较重要
                )
                return memory_id
            return None
        except Exception as e:
            logger.error(f"Extract and save failed: {e}")
            return None

    def run_clustering(self, agent_id: str) -> List[str]:
        """运行即时聚类并更新长期记忆"""
        try:
            cluster = ConceptCluster(agent_id)
            new_principles = cluster.cluster_and_abstract()
            
            if new_principles:
                sm = self._get_semantic_memory(agent_id)
                for principle in new_principles:
                    sm.add_core_principle(principle, importance=1.0)
                return new_principles
            return []
        except Exception as e:
            logger.error(f"Clustering run failed: {e}")
            return []

    def get_stats(self, agent_id: str) -> Dict:
        """获取统计信息"""
        wm = self._get_working_memory(agent_id)
        sm = self._get_semantic_memory(agent_id)
        
        return {
            "working_memory": {
                "count": len(wm.items),
                "tokens": wm.total_tokens()
            },
            "episodic_memory": {
                # Chroma count 需要在 episodic memory 暴露接口，这里简化
                "count": "dynamic"
            },
            "semantic_memory": {
                "core_principles": len(sm.core_principles)
            }
        }
