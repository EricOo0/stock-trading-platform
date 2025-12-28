import requests
import logging
import time
import jieba
import jieba.analyse
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class XueqiuTool:
    """
    Xueqiu Tool for scraping discussions and generating word cloud data.
    """

    BASE_URL = "https://xueqiu.com"
    SEARCH_URL = "https://xueqiu.com/query/v1/search/status.json"

    # Financial and common stop words to filter out generic terms
    STOP_WORDS = {
        "股份", "公司", "企业", "行业", "业务", "进行", "已经", "通过", "显示", "目前",
        "同时", "由于", "因为", "所以", "但是", "可能", "情况", "相关", "提供", "实现",
        "以及", "甚至", "不仅", "而且", "可以", "这个", "那个", "这些", "那些", "一个",
        "这种", "这样", "如何", "什么", "为什么", "大家", "觉得", "感觉", "观点", "讨论",
        "看看", "回复", "转载", "分享", "作者", "来源", "链接", "点击", "关注", "阅读",
        "平台", "用户", "发展", "核心", "战略", "提供", "合作", "服务", "进行", "已经",
        "由于", "目前", "通过", "实现", "不仅", "而且", "以及", "因此", "因为", "所以",
        "或者", "但是", "能够", "需要", "可以", "应当", "这种", "那样", "即使", "即便",
    }

    def __init__(
        self, base_url: Optional[str] = None, search_url: Optional[str] = None
    ):
        self.base_url = base_url or self.BASE_URL
        self.search_url = search_url or self.SEARCH_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": f"{self.base_url}/",
                "Connection": "keep-alive",
            }
        )
        self._cookies_fetched = False

    def _fetch_cookies(self):
        """Fetch initial cookies from Xueqiu home page and a stock page."""
        try:
            if not self._cookies_fetched:
                # 1. Visit home page
                self.session.get(self.base_url, timeout=10)
                # 2. Visit a stock page to get common cookies (like acw_tc)
                self.session.get(f"{self.base_url}/S/SH600519", timeout=10)
                self._cookies_fetched = True
                logger.info("Xueqiu cookies initialized.")
        except Exception as e:
            logger.error(f"Failed to fetch Xueqiu cookies: {e}")

    def search_discussions(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for discussions/posts on Xueqiu."""
        self._fetch_cookies()
        try:
            params = {
                "q": query,
                "count": limit,
                "page": 1,
                "sort": "relevance",
                "source": "all",
            }
            # For JSON API, we should use appropriate Accept header
            headers = {"Accept": "application/json, text/plain, */*"}
            response = self.session.get(
                self.search_url, params=params, timeout=10, headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Xueqiu search failed with status {response.status_code}")
                return []

            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                logger.error(
                    f"Xueqiu search returned non-JSON content: {content_type}. "
                    f"Possibly blocked by WAF. Snippet: {response.text[:200]}"
                )
                return []

            try:
                data = response.json()
                return data.get("list", [])
            except Exception as json_err:
                logger.error(
                    f"Failed to parse Xueqiu search JSON: {json_err}. "
                    f"Snippet: {response.text[:200]}"
                )
                return []
        except Exception as e:
            logger.error(f"Error searching Xueqiu: {e}")
            return []

    def get_wordcloud_data(
        self, query: str, limit: int = 50, finbert_tool=None, search_tool=None
    ) -> Dict[str, Any]:
        """
        Generate word cloud data from Xueqiu discussions.
        Returns a list of words with weights and sentiment.
        """
        posts = self.search_discussions(query, limit=limit)
        source_url = f"https://xueqiu.com/search?q={query}"
        source_name = "雪球网"

        if not posts:
            if search_tool:
                logger.info(
                    f"Xueqiu returned no results for '{query}', falling back to Tavily."
                )
                # Fallback to Tavily general search
                tavily_results = search_tool.search(
                    query, max_results=limit, topic="general"
                )
                if tavily_results:
                    posts = []
                    for res in tavily_results:
                        posts.append(
                            {"title": res.get("title", ""), "text": res.get("body", "")}
                        )
                    source_name = "Tavily Web Search"
                    source_url = tavily_results[0].get("href", source_url)

            if not posts:
                return {
                    "status": "error",
                    "message": f"未能从雪球网或搜索引擎获取关于 '{query}' 的讨论。请稍后再试或检查日志。",
                    "data": {"words": [], "summary": ""},
                }

        # 1. Extract and clean text
        all_text = []
        full_content_list = []
        for post in posts:
            text = post.get("text", "")
            title = post.get("title", "")
            # Remove HTML tags
            clean_text = re.sub(r"<[^>]+>", "", f"{title} {text}")
            # Remove URLs
            clean_text = re.sub(r"https?://[^\s]+", "", clean_text)
            if clean_text.strip():
                all_text.append(clean_text)
                full_content_list.append(clean_text)

        combined_text = " ".join(all_text)

        # 2. Extract keywords using TF-IDF and TextRank for better significance
        # TF-IDF highlights unique words, TextRank highlights core concepts
        tfidf_keywords = jieba.analyse.extract_tags(
            combined_text, topK=50, withWeight=True
        )
        textrank_keywords = jieba.analyse.textrank(
            combined_text, topK=50, withWeight=True
        )

        # Merge and deduplicate, filtering by STOP_WORDS and word length
        combined_keywords_dict = {word: weight for word, weight in tfidf_keywords}
        for word, weight in textrank_keywords:
            if word in combined_keywords_dict:
                combined_keywords_dict[word] += weight
            else:
                combined_keywords_dict[word] = weight

        filtered_keywords = []
        for word, weight in combined_keywords_dict.items():
            # Filter by length, stop words, and ensure it contains meaningful characters
            if (
                len(word) > 1
                and word not in self.STOP_WORDS
                and re.search(r"[\u4e00-\u9fa5a-zA-Z0-9]", word)
            ):
                filtered_keywords.append((word, weight))

        filtered_keywords.sort(key=lambda x: x[1], reverse=True)
        keywords = filtered_keywords[:30]

        if not keywords:
            return {
                "status": "success",
                "data": {"words": [], "summary": "No significant keywords found."},
            }

        # 3. Analyze sentiment for each keyword
        # We look for sentences containing the keyword and score them
        word_data = []
        summary_parts = []

        for word, weight in keywords:
            sentiment = "neutral"
            if finbert_tool:
                # Find sentences with this word to get context-specific sentiment
                context_sentences = []
                for text in full_content_list:
                    if word in text:
                        # Extract a snippet around the word
                        idx = text.find(word)
                        start = max(0, idx - 50)
                        end = min(len(text), idx + 50)
                        context_sentences.append({"title": text[start:end]})

                if context_sentences:
                    analysis = finbert_tool.analyze(
                        context_sentences[:5]
                    )  # Sample up to 5 contexts
                    if analysis.get("score", 50) > 60:
                        sentiment = "positive"
                    elif analysis.get("score", 50) < 40:
                        sentiment = "negative"

            word_data.append(
                {"text": word, "value": int(weight * 100), "sentiment": sentiment}
            )

        # 4. Create summary
        top_words = [w["text"] for w in word_data[:5]]
        pos_words = [w["text"] for w in word_data if w["sentiment"] == "positive"][:3]
        neg_words = [w["text"] for w in word_data if w["sentiment"] == "negative"][:3]

        summary = f"基于{source_name}对 '{query}' 的讨论分析，当前社交媒体关注核心词包括：{', '.join(top_words)}。"
        if pos_words:
            summary += f" 正面情绪点主要集中在：{', '.join(pos_words)}。"
        if neg_words:
            summary += f" 负向担忧点涉及：{', '.join(neg_words)}。"

        return {
            "status": "success",
            "data": {
                "words": word_data,
                "summary": summary,
                "source_url": source_url,
            },
        }


if __name__ == "__main__":
    import sys
    import os
    import json

    # 1. 自动处理 PYTHONPATH，确保在 backend/infrastructure/market 目录下也能直接运行
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 2. 配置日志输出到控制台
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 3. 动态加载依赖项（避免循环引用）
    try:
        from backend.infrastructure.search.tavily import TavilyTool
        from backend.infrastructure.config.loader import config

        tavily_key = config.get_api_key("tavily")
        search_tool = TavilyTool(tavily_key) if tavily_key else None
    except ImportError:
        logger.warning("Could not load TavilyTool/Config for fallback testing.")
        search_tool = None

    # 4. 获取查询参数并运行
    query = sys.argv[1] if len(sys.argv) > 1 else "贵州茅台 近期股价"
    tool = XueqiuTool()

    print(f"\n>>> 开始测试雪球分析工具 (查询: {query})")
    data = tool.get_wordcloud_data(query, search_tool=search_tool)

    # 5. 美化输出结果
    print("\n>>> 分析结果:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
