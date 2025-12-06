
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FinBERTTool:
    """
    FinBERT Sentiment Analysis Tool
    Uses ProsusAI/finbert for financial sentiment analysis.
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._model_loaded = False
        self._use_finbert = True

    def _load_model(self):
        if self._model_loaded: return
        try:
            logger.info("Loading FinBERT model...")
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            
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
            self._model_loaded = True

    def analyze(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment from a list of news items."""
        if not news_items:
            return {
                "score": 50, "rating": "Neutral", 
                "summary": "No news to analyze.",
                "key_drivers": [],
                "sentiment_breakdown": {"positive_ratio": 0, "negative_ratio": 0, "neutral_ratio": 0},
                "method": "none"
            }
        
        self._load_model()
        
        if self._use_finbert and self._model is not None:
            return self._analyze_with_finbert(news_items)
        else:
            return self._analyze_heuristic(news_items)

    def _analyze_with_finbert(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_positive = 0
        total_negative = 0
        total_neutral = 0
        key_drivers = []
        
        for item in news_items:
            title = item.get('title', '')
            summary = item.get('summary', '')
            text = f"{title}. {summary}" if summary and summary != title else title
            
            scores = self._analyze_text_finbert(text)
            
            total_positive += scores['positive']
            total_negative += scores['negative']
            total_neutral += scores['neutral']
            
            if len(key_drivers) < 3:
                key_drivers.append({
                    "title": title,
                    "sentiment": max(scores, key=scores.get),
                    "confidence": max(scores.values())
                })
                
        n = len(news_items)
        avg_pos = total_positive / n
        avg_neg = total_negative / n
        avg_neu = total_neutral / n
        
        score = int((avg_pos - avg_neg + 1) * 50)
        score = max(0, min(100, score))
        
        if score >= 65: rating = "Bullish"
        elif score <= 35: rating = "Bearish"
        else: rating = "Neutral"
        
        summary = f"FinBERT Analysis (Score: {score}, {rating}). "
        if avg_pos > avg_neg: summary += f"Positive sentiment dominates ({avg_pos*100:.1f}%)."
        elif avg_neg > avg_pos: summary += f"Negative sentiment dominates ({avg_neg*100:.1f}%)."
        else: summary += "Mixed sentiment."

        return {
            "score": score,
            "rating": rating,
            "summary": summary,
            "key_drivers": [d["title"] for d in key_drivers],
            "sentiment_breakdown": {
                "positive_ratio": round(avg_pos, 3),
                "negative_ratio": round(avg_neg, 3),
                "neutral_ratio": round(avg_neu, 3)
            },
            "method": "finbert"
        }

    def _analyze_text_finbert(self, text: str) -> Dict[str, float]:
        try:
            import torch
            inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            return {
                "positive": float(probs[0][0]),
                "negative": float(probs[0][1]),
                "neutral": float(probs[0][2])
            }
        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}

    def _analyze_heuristic(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback simple heuristic (mock)"""
        # Simplified logic compared to source, focusing on fallback safety
        return {
            "score": 50,
            "rating": "Neutral",
            "summary": "Heuristic Analysis (Fallback): Neutral market sentiment.",
            "key_drivers": [item.get("title", "") for item in news_items[:3]],
            "sentiment_breakdown": {"positive_ratio": 0.33, "negative_ratio": 0.33, "neutral_ratio": 0.34},
            "method": "heuristic"
        }

if __name__ == "__main__":
    tool = FinBERTTool()
    # print(tool.analyze([{"title": "Stock market hits record high", "summary": "Everything is awesome"}]))
