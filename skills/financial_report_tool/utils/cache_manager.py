"""
缓存管理器
用于缓存财务数据,减少API调用
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger

class CacheManager:
    """简单的文件缓存管理器"""
    
    def __init__(self, cache_dir: str = ".cache/financial_data", ttl_hours: int = 24):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            ttl_hours: 缓存有效期(小时)
        """
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        
        # 创建缓存目录
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create cache directory: {e}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键 (通常是symbol)
            
        Returns:
            缓存的数据,如果不存在或过期则返回None
        """
        cache_file = self._get_cache_file(key)
        
        if not os.path.exists(cache_file):
            logger.debug(f"Cache miss for {key}")
            return None
        
        try:
            # 检查是否过期
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - mtime > self.ttl:
                logger.debug(f"Cache expired for {key}")
                os.remove(cache_file)
                return None
            
            # 读取缓存
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Cache hit for {key}")
                return data
                
        except Exception as e:
            logger.warning(f"Error reading cache for {key}: {e}")
            return None
    
    def set(self, key: str, data: Dict[str, Any]):
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 要缓存的数据
        """
        cache_file = self._get_cache_file(key)
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cached data for {key}")
        except Exception as e:
            logger.warning(f"Error writing cache for {key}: {e}")
    
    def clear(self, key: Optional[str] = None):
        """
        清除缓存
        
        Args:
            key: 如果指定,只清除该键的缓存;否则清除所有缓存
        """
        try:
            if key:
                cache_file = self._get_cache_file(key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    logger.info(f"Cleared cache for {key}")
            else:
                # 清除所有缓存
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                logger.info("Cleared all cache")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def _get_cache_file(self, key: str) -> str:
        """获取缓存文件路径"""
        # 清理key中的特殊字符
        safe_key = key.replace('/', '_').replace('.', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.json")
