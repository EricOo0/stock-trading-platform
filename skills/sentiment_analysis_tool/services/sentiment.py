import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SentimentService:
    """Service to analyze market sentiment from news using FinBERT"""

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._model_loaded = False
        self._use_finbert = True
        
    def _load_model(self):
        """Lazy load FinBERT model on first use"""
        if self._model_loaded:
            return
            
        try:
            logger.info("Loading FinBERT model...")
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            # Load FinBERT model and tokenizer
            model_name = "ProsusAI/finbert"
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self._model.eval()
            
            self._model_loaded = True
            logger.info("FinBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            logger.warning("Falling back to heuristic sentiment analysis")
            self._use_finbert = False
            self._model_loaded = True  # Mark as loaded to avoid retry

    def _analyze_text_finbert(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of a single text using FinBERT"""
        try:
            import torch
            
            # Tokenize and prepare input
            inputs = self._tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512,
                padding=True
            )
            
            # Get predictions
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT output: [positive, negative, neutral]
            sentiment_scores = {
                "positive": float(probs[0][0]),
                "negative": float(probs[0][1]),
                "neutral": float(probs[0][2])
            }
            
            return sentiment_scores
            
        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            # Return neutral scores on error
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}

    def _analyze_heuristic(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback heuristic analysis (original implementation)"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for item in news_items:
            sentiment = item.get("mock_sentiment", "neutral")
            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(news_items)
        raw_score = 50 + (positive_count * 10) - (negative_count * 10)
        score = max(0, min(100, raw_score))
        
        if score >= 65:
            rating = "Bullish"
        elif score <= 35:
            rating = "Bearish"
        else:
            rating = "Neutral"
        
        return {
            "score": score,
            "rating": rating,
            "method": "heuristic"
        }

    def analyze(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment from a list of news items.
        
        Args:
            news_items: List of news dictionaries
            
        Returns:
            Dictionary containing:
            - score: 0-100 (0=Bearish, 50=Neutral, 100=Bullish)
            - rating: Bearish/Neutral/Bullish
            - summary: Text summary
            - key_drivers: List of key events
            - sentiment_breakdown: Detailed scores
        """
        if not news_items:
            return {
                "score": 50,
                "rating": "Neutral",
                "summary": "暂无相关新闻，无法评估市场情绪。",
                "key_drivers": [],
                "sentiment_breakdown": {
                    "positive_ratio": 0,
                    "negative_ratio": 0,
                    "neutral_ratio": 0
                },
                "method": "none"
            }
        
        # Ensure model is loaded
        self._load_model()
        
        # Use FinBERT if available, otherwise fallback to heuristic
        if self._use_finbert and self._model is not None:
            return self._analyze_with_finbert(news_items)
        else:
            result = self._analyze_heuristic(news_items)
            # Add missing fields for consistency
            result["summary"] = f"基于启发式算法分析{len(news_items)}条新闻，市场情绪整体表现为{result['rating']}（得分：{result['score']}）。"
            result["key_drivers"] = [item["title"] for item in news_items[:3]]
            result["sentiment_breakdown"] = {
                "positive_ratio": 0,
                "negative_ratio": 0,
                "neutral_ratio": 0
            }
            return result

    def _analyze_with_finbert(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze news items using FinBERT model"""
        total_positive = 0
        total_negative = 0
        total_neutral = 0
        
        key_drivers = []
        
        for item in news_items:
            # Combine title and summary for analysis
            text = f"{item['title']}. {item.get('summary', '')}"
            
            # Analyze with FinBERT
            scores = self._analyze_text_finbert(text)
            
            total_positive += scores['positive']
            total_negative += scores['negative']
            total_neutral += scores['neutral']
            
            # Track top drivers (limit to 3)
            if len(key_drivers) < 3:
                key_drivers.append({
                    "title": item["title"],
                    "sentiment": max(scores, key=scores.get),
                    "confidence": max(scores.values())
                })
        
        # Calculate averages
        n = len(news_items)
        avg_positive = total_positive / n
        avg_negative = total_negative / n
        avg_neutral = total_neutral / n
        
        # Convert to 0-100 scale
        # Formula: (positive - negative + 1) * 50
        # When positive=1, negative=0: score=100
        # When positive=0, negative=1: score=0
        # When positive=negative: score=50
        score = int((avg_positive - avg_negative + 1) * 50)
        score = max(0, min(100, score))
        
        # Determine rating
        if score >= 65:
            rating = "Bullish"
        elif score <= 35:
            rating = "Bearish"
        else:
            rating = "Neutral"
        
        # Generate summary
        summary = f"基于FinBERT模型分析{n}条新闻，市场情绪整体表现为{rating}（得分：{score}）。"
        if avg_positive > avg_negative:
            summary += f" 正面情绪占主导（{avg_positive*100:.1f}%），主要涉及{key_drivers[0]['title'] if key_drivers else '市场动态'}等方面。"
        elif avg_negative > avg_positive:
            summary += f" 负面情绪较强（{avg_negative*100:.1f}%），主要受到{key_drivers[0]['title'] if key_drivers else '市场担忧'}等因素影响。"
        else:
            summary += " 正负面消息交织，市场处于观望状态。"
        
        return {
            "score": score,
            "rating": rating,
            "summary": summary,
            "key_drivers": [d["title"] for d in key_drivers],
            "sentiment_breakdown": {
                "positive_ratio": round(avg_positive, 3),
                "negative_ratio": round(avg_negative, 3),
                "neutral_ratio": round(avg_neutral, 3)
            },
            "method": "finbert"
        }
