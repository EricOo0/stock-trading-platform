import datetime
import logging
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select
from backend.app.agents.personal_finance.db import engine
from backend.app.agents.personal_finance.db_models import (
    DecisionRecord,
    LessonRecord,
    Portfolio,
)
from backend.app.agents.personal_finance.models import RecommendationCard
from backend.app.agents.personal_finance.task_schemas import (
    LessonItem,
    DecisionReviewResult,
)
from backend.app.registry import Tools

logger = logging.getLogger(__name__)

class PersonalFinanceRepository:
    def __init__(self):
        self.engine = engine
        self.registry = Tools()

    def get_active_decisions(self, user_id: str) -> List[DecisionRecord]:
        with Session(self.engine) as session:
            stmt = select(DecisionRecord).where(
                DecisionRecord.user_id == user_id,
                DecisionRecord.status == "active",
            )
            return list(session.exec(stmt).all())

    def get_lessons(self, user_id: str) -> List[LessonRecord]:
        with Session(self.engine) as session:
            stmt = select(LessonRecord).where(LessonRecord.user_id == user_id)
            return list(session.exec(stmt).all())

    def get_portfolio(self, user_id: str) -> Optional[Dict[str, Any]]:
        with Session(self.engine) as session:
            stmt = select(Portfolio).where(Portfolio.user_id == user_id)
            port_obj = session.exec(stmt).first()
            if port_obj:
                assets = []
                for a in port_obj.assets:
                    assets.append(a.model_dump())
                port_data = port_obj.model_dump()
                port_data["assets"] = assets
                return port_data
        return None

    def save_decisions(self, user_id: str, cards: List[RecommendationCard]):
        if not cards:
            return

        with Session(self.engine) as session:
            today = datetime.datetime.utcnow().date()
            
            for card in cards:
                symbol = card.asset_id
                if not symbol:
                    continue
                    
                # Attempt to get current price for reference
                current_price = 0.0
                try:
                    price_data = self.registry.get_stock_price(symbol)
                    if isinstance(price_data, dict):
                        current_price = float(price_data.get("current_price", 0.0))
                    elif isinstance(price_data, (int, float)):
                        current_price = float(price_data)
                except Exception as e:
                    logger.warning(f"[Repository] Could not fetch price for {symbol} when saving decision: {e}")

                # Check for existing active record for TODAY
                stmt = select(DecisionRecord).where(
                    DecisionRecord.user_id == user_id,
                    DecisionRecord.symbol == symbol,
                    DecisionRecord.status == "active"
                )
                existing_records = list(session.exec(stmt).all())
                
                record_to_update = None
                for rec in existing_records:
                    if rec.created_at.date() == today:
                        record_to_update = rec
                        break
                
                if record_to_update:
                    # Update existing
                    record_to_update.action = card.action.value if hasattr(card.action, "value") else str(card.action)
                    record_to_update.price_at_suggestion = current_price
                    record_to_update.reasoning = f"{card.title}: {card.description}"
                    record_to_update.created_at = datetime.datetime.utcnow()
                    session.add(record_to_update)
                    logger.info(f"[Repository] Updated existing active decision for {symbol}")
                else:
                    # Create new
                    record = DecisionRecord(
                        user_id=user_id,
                        symbol=symbol,
                        action=card.action.value if hasattr(card.action, "value") else str(card.action),
                        price_at_suggestion=current_price,
                        reasoning=f"{card.title}: {card.description}",
                        status="active"
                    )
                    session.add(record)
            
            session.commit()

    def save_lessons(self, user_id: str, lessons: List[LessonItem]):
        if not lessons:
            return

        with Session(self.engine) as session:
            # Delete old lessons
            stmt = select(LessonRecord).where(LessonRecord.user_id == user_id)
            existing = session.exec(stmt).all()
            for r in existing:
                session.delete(r)
            
            # Add new
            for l in lessons:
                rec = LessonRecord(
                    user_id=user_id,
                    title=l.title,
                    description=l.description,
                    confidence=l.confidence or 1.0
                )
                session.add(rec)
            session.commit()

    def update_decision_reviews(self, user_id: str, reviews: List[DecisionReviewResult]):
        if not reviews:
            return

        with Session(self.engine) as session:
            for rev in reviews:
                rec = session.get(DecisionRecord, rev.decision_id)
                if rec and rec.user_id == user_id:
                    rec.review_result = "correct" if rev.is_correct else "incorrect"
                    rec.review_comment = rev.reason
                    session.add(rec)
            session.commit()
