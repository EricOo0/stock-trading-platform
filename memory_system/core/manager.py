import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from .working_memory import WorkingMemory
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .compressor import compressor
from .extractor import extractor
from .cluster import ConceptCluster
from config import settings
from utils.logger import logger
from utils.tokenizer import tokenizer


class MemoryManager:
    """
    记忆系统核心管理器
    负责协调三层记忆系统，为每个 Agent 维护独立的记忆实例
    """

    _instances: Dict[str, "MemoryManager"] = {}

    def __init__(self):
        # 按 user_id:agent_id 存储记忆实例
        self.working_memories: Dict[str, WorkingMemory] = {}
        self.episodic_memories: Dict[str, EpisodicMemory] = {}
        self.semantic_memories: Dict[str, SemanticMemory] = {}
        
        # 异步任务队列与状态追踪
        self.task_queue = asyncio.Queue()
        self.task_states: Dict[str, Dict] = {}
        self._worker_task = None
        
        logger.info("MemoryManager initialized")

    @classmethod
    def get_instance(cls) -> "MemoryManager":
        if "default" not in cls._instances:
            cls._instances["default"] = cls()
        return cls._instances["default"]

    def _ensure_worker_started(self):
        """确保后台 Worker 已启动"""
        if self._worker_task is None or self._worker_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._worker_task = loop.create_task(self._background_worker())
                logger.info("Background Memory Worker started")
            except RuntimeError:
                logger.warning("No running event loop found, worker not started")

    async def _background_worker(self):
        """后台任务处理器"""
        logger.info("Memory Worker loop started")
        while True:
            task = await self.task_queue.get()
            task_id = task.get("task_id")
            try:
                task_type = task.get("type")
                user_id = task.get("user_id")
                agent_id = task.get("agent_id")
                
                self.task_states[task_id] = {
                    "status": "processing",
                    "start_time": datetime.now().isoformat()
                }
                
                if task_type == "finalize":
                    await self._process_finalize_task(user_id, agent_id)
                
                self.task_states[task_id]["status"] = "completed"
                self.task_states[task_id]["end_time"] = datetime.now().isoformat()
                logger.info(f"Task {task_id} ({task_type}) completed")
                
            except Exception as e:
                logger.error(f"Error in background task {task_id}: {e}")
                self.task_states[task_id] = {
                    "status": "failed",
                    "error": str(e),
                    "end_time": datetime.now().isoformat()
                }
            finally:
                self.task_queue.task_done()

    async def _process_finalize_task(self, user_id: str, agent_id: str):
        """实际执行结算逻辑的私有方法"""
        wm = self._get_working_memory(user_id, agent_id)
        
        # 仅获取尚未结算的新增语料
        new_items = wm.get_unfinalized_details()
        if not new_items:
            logger.info(f"No new items to finalize for {user_id}")
            return

        # 使用 asyncio.to_thread 将同步阻塞的 LLM/DB 操作移出主事件循环，防止阻塞其他用户请求
        # 1. 触发压缩与提取流水线 (MTM 转化) - 基于新增内容
        await asyncio.to_thread(self._handle_compression, user_id, agent_id, new_items)

        # 2. 触发用户画像更新 (LTM 转化) - 基于新增内容
        await asyncio.to_thread(self._handle_persona_update, user_id, agent_id, new_items)

        # 3. 触发长期原则聚类 (LTM 转化)
        await asyncio.to_thread(self.run_clustering, user_id, agent_id)

        # 4. 执行垃圾回收 (GC)
        await asyncio.to_thread(self.perform_garbage_collection, user_id, agent_id)

        # 5. 标记为已结算
        wm.mark_finalized()
        
        # 6. 清理陈旧记忆，但保留最近 5 轮作为热启动上下文 (Cross-session continuity)
        wm.clear(keep_last_n=5)

    def perform_garbage_collection(self, user_id: str, agent_id: str):
        """
        执行记忆清理 (GC)
        移除低重要度且陈旧的中期记忆，保持系统轻量
        """
        try:
            em = self._get_episodic_memory(user_id, agent_id)
            count = em.vector_store.count()
            
            # 设定软上限，超过则触发清理
            SOFT_LIMIT = 1000
            if count > SOFT_LIMIT:
                logger.info(f"Memory GC triggered for {user_id}:{agent_id} (Count: {count})")
                # 简单策略：按索引顺序（通常是时间顺序）删除最旧的 10%
                to_delete_count = int(count * 0.1)
                results = em.vector_store.collection.get(
                    limit=to_delete_count,
                    include=["metadatas"]
                )
                if results["ids"]:
                    em.vector_store.delete(ids=results["ids"])
                    logger.info(f"GC deleted {len(results['ids'])} old episodic memories")
        except Exception as e:
            logger.error(f"Memory GC failed: {e}")

    def finalize_session(self, user_id: str, agent_id: str) -> Dict[str, Any]:
        """
        结算当前会话 (异步化改版)：
        将结算任务压入队列并立即返回
        """
        try:
            self._ensure_worker_started()
            task_id = str(uuid.uuid4())
            
            task = {
                "task_id": task_id,
                "type": "finalize",
                "user_id": user_id,
                "agent_id": agent_id,
                "created_at": datetime.now().isoformat()
            }
            
            # 将任务放入队列 (同步方法中使用 put_nowait)
            self.task_queue.put_nowait(task)
            
            self.task_states[task_id] = {
                "status": "queued",
                "created_at": task["created_at"]
            }
            
            logger.info(f"🏁 Finalize session queued for user {user_id}. Task ID: {task_id}")
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Session finalization started in background"
            }
        except Exception as e:
            logger.error(f"Failed to queue finalize session: {e}")
            return {"status": "error", "message": str(e)}

    def add_memory(self, user_id: str, agent_id: str, content: Any, role: str = "user", memory_type: str = "conversation", metadata: Dict = None) -> Dict:
        """添加新记忆到 Working Memory"""
        wm = self._get_working_memory(user_id, agent_id)
        
        # 绑定压缩回调 (如果还没绑定)
        if not wm.compression_callback:
            wm.set_compression_callback(lambda items: self._handle_compression(user_id, agent_id, items))
            
        memory_id = str(uuid.uuid4())
        memory_item = {
            "id": memory_id,
            "content": content,
            "role": role,
            "metadata": metadata or {}
        }
        wm.add(memory_item)
        
        return {
            "status": "success", 
            "memory_id": memory_id,
            "stored_in": ["working_memory"],
            "tokens": wm.total_tokens()
        }

    def get_context(self, user_id: str, agent_id: str, query: str, session_id: str = None, limit: int = 20, max_tokens: int = 5000) -> Dict:
        """获取三层记忆复合上下文，包含 Token 预算控制"""
        wm = self._get_working_memory(user_id, agent_id)
        em = self._get_episodic_memory(user_id, agent_id)
        sm = self._get_semantic_memory(user_id, agent_id)
        
        budget = settings.TOKEN_BUDGET
        
        # 1. STM - 近期对话 (Working Memory)
        # 应用 max_tokens 限制 (从最新消息开始保留)
        full_items = wm.get_details()
        working_items = []
        working_tokens = 0
        
        # 从后往前遍历，直到 token 超限
        for item in reversed(full_items):
            content_str = f"{item.get('role', '')}: {str(item.get('content', ''))}"
            t_count = tokenizer.count_tokens(content_str)
            if working_tokens + t_count > max_tokens:
                break
            working_items.insert(0, item)
            working_tokens += t_count
        
        # 2. MTM - 相关见解 (Episodic Memory)
        # 使用 limit 参数限制条数
        episodic_results = em.retrieve(query, top_k=limit) 
        episodic_items = []
        episodic_tokens = 0
        for m in episodic_results:
            item_tokens = tokenizer.count_tokens(m["content"])
            if episodic_tokens + item_tokens > budget.get("episodic_memory", 20000):
                break
            episodic_items.append({
                "content": m["content"], 
                "metadata": m["metadata"], 
                "score": m["score"]
            })
            episodic_tokens += item_tokens
            
        # 3. LTM - 画像、原则与经验 (Semantic Memory)
        core_principles = sm.get_core_principles()
        principles_tokens = tokenizer.count_tokens(core_principles)
        
        user_persona_data = sm.user_persona
        persona_summary = sm.get_persona_summary()
        persona_tokens = tokenizer.count_tokens(persona_summary)
        
        # 语义检索相关经验 (Semantic Results)
        semantic_results = sm.retrieve_relevant_experiences(query, top_k=5)
        semantic_items = []
        semantic_tokens = 0
        for m in semantic_results:
            item_tokens = tokenizer.count_tokens(m["content"])
            if semantic_tokens + item_tokens > budget.get("semantic_memory", 500):
                break
            semantic_items.append(f"- {m['content']}")
            semantic_tokens += item_tokens
            
        semantic_context = "\n".join(semantic_items)
        
        # 合并 Semantic Memory 部分
        full_semantic = f"{persona_summary}\n\nPrinciples:\n{core_principles}\n\nRelevant Experience:\n{semantic_context}"
        total_semantic_tokens = persona_tokens + principles_tokens + semantic_tokens
        
        return {
            "working_memory": working_items,
            "episodic_memory": episodic_items,
            "semantic_memory": full_semantic,
            "user_persona": user_persona_data,
            "core_principles": core_principles,
            "token_usage": {
                "working_memory": working_tokens,
                "core_principles": principles_tokens,
                "episodic_memory": episodic_tokens,
                "semantic_memory": total_semantic_tokens,
                "total": working_tokens + episodic_tokens + total_semantic_tokens
            }
        }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取异步任务执行状态"""
        return self.task_states.get(task_id, {"status": "not_found"})

    def get_all_identities(self) -> Dict[str, List[str]]:
        """获取系统中存在的所有 User 和 Agent 列表 (通过扫描数据文件)"""
        import os
        from config import settings
        
        users = set()
        agents = set()
        
        # 1. 扫描 Working Memory 文件 (最准确)
        data_dir = settings.DATA_DIR
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.startswith("working_") and filename.endswith(".json"):
                    # working_{user_id}_{agent_id}.json
                    # 去掉前缀 working_ (8 chars) 和后缀 .json (5 chars)
                    content_part = filename[8:-5]
                    
                    # 尝试匹配已知 Agent
                    known_agents = ["research_agent", "chairman", "market", "macro", "sentiment", "web_search", "receptionist", "researcher"]
                    found_agent = None
                    for ka in known_agents:
                        if content_part.endswith(f"_{ka}"):
                            found_agent = ka
                            break
                    
                    if found_agent:
                        agent_id = found_agent
                        user_id = content_part[: -(len(found_agent) + 1)]
                        if user_id:
                            users.add(user_id)
                            agents.add(agent_id)
                    else:
                        # 降级：假设最后一节是 agent_id
                        parts = content_part.split("_")
                        if len(parts) >= 2:
                            agents.add(parts[-1])
                            users.add("_".join(parts[:-1]))

        # 2. 补充内存中当前的
        for key in self.working_memories.keys():
            if ":" in key:
                u, a = key.split(":", 1)
                users.add(u)
                agents.add(a)
                
        # 3. 确保默认值存在 (已移除，以便准确反映系统状态)
        # if not users: users.add("test_user_001")
        # if not agents: 
        #     agents.add("research_agent")
        #     agents.add("chairman")
                
        return {
            "users": sorted(list(users)),
            "agents": sorted(list(agents))
        }

    def get_stats(self, user_id: str, agent_id: str) -> Dict:
        """获取统计信息"""
        wm = self._get_working_memory(user_id, agent_id)
        sm = self._get_semantic_memory(user_id, agent_id)

        return {
            "working_memory": {"count": len(wm.items), "tokens": wm.total_tokens()},
            "episodic_memory": {"count": "dynamic"},
            "semantic_memory": {"core_principles": len(sm.core_principles)},
        }

    def _get_working_memory(self, user_id: str, agent_id: str) -> WorkingMemory:
        key = f"{user_id}:{agent_id}"
        if key not in self.working_memories:
            self.working_memories[key] = WorkingMemory(user_id, agent_id)
        return self.working_memories[key]

    def _get_episodic_memory(self, user_id: str, agent_id: str) -> EpisodicMemory:
        key = f"{user_id}:{agent_id}"
        if key not in self.episodic_memories:
            self.episodic_memories[key] = EpisodicMemory(user_id, agent_id)
        return self.episodic_memories[key]

    def _get_semantic_memory(self, user_id: str, agent_id: str) -> SemanticMemory:
        key = f"{user_id}:{agent_id}"
        if key not in self.semantic_memories:
            self.semantic_memories[key] = SemanticMemory(user_id, agent_id)
        return self.semantic_memories[key]

    def _handle_compression(self, user_id: str, agent_id: str, items: List[Dict]):
        """处理记忆压缩与中期记忆提取"""
        em = self._get_episodic_memory(user_id, agent_id)
        
        # 提取投资见解
        full_text = "\n".join([f"{item['role']}: {item['content']}" for item in items])
        insight = extractor.extract_investment_insight(full_text)
        
        if insight and insight.get("symbol"):
            # 将关键维度存入 metadata 以便后续分析
            metadata = {
                "symbol": insight["symbol"],
                "viewpoint": insight.get("viewpoint"),
                "confidence": insight.get("confidence", 0.5)
            }
            em.add_event(
                event_type="InvestmentInsight",
                content=insight,
                entities=[insight["symbol"]],
                importance=insight.get("confidence", 0.5),
                metadata_extra=metadata # 假设 add_event 支持这个
            )
            logger.info(f"Extracted investment insight for {insight['symbol']} ({insight.get('viewpoint')})")

        # 提取通用事件
        event = extractor.extract(full_text)
        if event:
            em.add_event(
                event_type=event.get("event_type", "General"),
                content=event,
                entities=event.get("entities", []),
                importance=0.4
            )

    def _handle_persona_update(self, user_id: str, agent_id: str, items: List[Dict]):
        """从对话中提取并更新用户画像"""
        sm = self._get_semantic_memory(user_id, agent_id)
        conversation_text = "\n".join([f"{item['role']}: {item['content']}" for item in items])
        
        new_traits = extractor.extract_user_persona(conversation_text)
        if new_traits:
            sm.update_persona(new_traits)

    def run_clustering(self, user_id: str, agent_id: str):
        """运行聚类算法提取长期原则"""
        clusterer = ConceptCluster(user_id, agent_id)
        principles = clusterer.cluster_and_abstract()
        
        if principles:
            sm = self._get_semantic_memory(user_id, agent_id)
            for p in principles:
                sm.add_core_principle(p)

    def clear_memory(self, user_id: str, agent_id: str) -> Dict[str, Any]:
        """清空指定用户和Agent的所有记忆"""
        try:
            # 1. 清空短期记忆
            wm = self._get_working_memory(user_id, agent_id)
            wm.clear(keep_last_n=0)
            
            # 2. 清空中期记忆
            em = self._get_episodic_memory(user_id, agent_id)
            em.clear()
            
            # 3. 清空长期记忆
            sm = self._get_semantic_memory(user_id, agent_id)
            sm.clear()
            
            logger.info(f"Memory cleared for {user_id}:{agent_id}")
            return {"status": "success", "message": "All memory cleared"}
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return {"status": "error", "message": str(e)}
