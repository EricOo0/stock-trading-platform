import networkx as nx
import json
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path
from config import settings
from utils.logger import logger

class GraphStore:
    """图存储包装类 (NetworkX)"""
    
    def __init__(self, graph_file: str = "knowledge_graph.json"):
        """
        初始化图存储
        
        Args:
            graph_file: 图数据持久化文件名
        """
        self.file_path = settings.DATA_DIR / graph_file
        self.graph = nx.MultiDiGraph()
        self._load()
        logger.info(f"GraphStore initialized (Nodes: {self.graph.number_of_nodes()})")

    def _load(self) -> None:
        """从文件加载图数据"""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Explicitly specify edges key to suppress warning and ensure compatibility
                    self.graph = nx.node_link_graph(data, edges="edges")
                logger.debug(f"Loaded graph from {self.file_path}")
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
                # 出错时使用空图
                self.graph = nx.MultiDiGraph()

    def _save(self) -> None:
        """保存图数据到文件"""
        try:
            # Explicitly specify edges key
            data = nx.node_link_data(self.graph, edges="edges")
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved graph to {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")

    def add_event(self, event_id: str, entities: List[str], relations: List[Tuple[str, str, str]], timestamp: str, weight: float = 1.0) -> None:
        """
        添加事件到图谱
        
        Args:
            event_id: 事件ID
            entities: 实体列表
            relations: 关系三元组 (subject, predicate, object)
            timestamp: 时间戳
            weight: 权重
        """
        try:
            # 添加实体节点
            for entity in entities:
                if not self.graph.has_node(entity):
                    self.graph.add_node(entity, type="entity")
            
            # 添加关系边
            for subject, predicate, obj in relations:
                # 确保节点存在
                if not self.graph.has_node(subject):
                    self.graph.add_node(subject, type="entity")
                if not self.graph.has_node(obj):
                    self.graph.add_node(obj, type="entity")
                    
                # 添加边
                self.graph.add_edge(
                    subject, obj,
                    relation=predicate,
                    event_id=event_id,
                    timestamp=str(timestamp),
                    weight=weight
                )
            
            self._save()
        except Exception as e:
            logger.error(f"Failed to add event to graph: {e}")
            raise

    def get_related_entities(self, entities: List[str], max_depth: int = 1) -> List[str]:
        """
        获取相关实体（扩展邻居）
        """
        if not entities:
            return []
            
        related = set(entities)
        try:
            for entity in entities:
                if self.graph.has_node(entity):
                    # 获取指定深度的邻居
                    if max_depth == 1:
                        neighbors = list(self.graph.neighbors(entity))
                        related.update(neighbors)
                    else:
                        # 广度优先搜索
                        paths = nx.single_source_shortest_path_length(
                            self.graph, entity, cutoff=max_depth
                        )
                        related.update(paths.keys())
            return list(related)
        except Exception as e:
            logger.error(f"Failed to get related entities: {e}")
            return list(related)

    def find_path(self, start: str, end: str, max_depth: int = 3) -> List[Any]:
        """查找两点间路径"""
        try:
            if not self.graph.has_node(start) or not self.graph.has_node(end):
                return []
            return list(nx.all_simple_paths(self.graph, start, end, cutoff=max_depth))
        except Exception as e:
            logger.error(f"Path finding failed: {e}")
            return []
            
    def get_stats(self) -> Dict:
        """获取图谱统计信息"""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges()
        }
