import datetime
import logging
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select
from backend.app.agents.personal_finance.db import engine
from backend.app.agents.personal_finance.db_models import (
    DecisionRecord,
    LessonRecord,
    Portfolio,
    ShadowPortfolio,
    ShadowAsset
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

    def save_decisions(self, user_id: str, cards: List[RecommendationCard]) -> List[Dict[str, Any]]:
        """
        Save decisions and return list of shadow trade requests (delta).
        """
        if not cards:
            return []

        shadow_requests = []

        with Session(self.engine) as session:
            today = datetime.datetime.utcnow().date()
            
            for card in cards:
                symbol = card.suggested_symbol or card.asset_id
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

                # Use suggested price if available, else current price
                exec_price = card.suggested_price if card.suggested_price else current_price
                new_qty = card.suggested_quantity or 0.0
                action_str = card.action.value if hasattr(card.action, "value") else str(card.action)

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
                
                delta_qty = 0.0
                trade_action = action_str

                if record_to_update:
                    # --- Update existing ---
                    old_qty = record_to_update.suggested_quantity
                    
                    # Check if action direction changed?
                    # If changed from Buy to Sell, we need to reverse old qty and apply new qty?
                    # This is complex. Let's simplify:
                    # We assume action direction is consistent or we use delta.
                    
                    # Case 1: Same Action (e.g. Buy -> Buy)
                    if record_to_update.action.lower() == action_str.lower():
                        if new_qty > old_qty:
                            delta_qty = new_qty - old_qty
                            trade_action = action_str
                        elif new_qty < old_qty:
                            # Reduced quantity? Means we over-bought?
                            # If Buy 1000 -> Buy 800, we should Sell 200.
                            delta_qty = old_qty - new_qty
                            trade_action = "sell" if action_str.lower() == "buy" else "buy"
                    else:
                        # Case 2: Action Changed (e.g. Buy -> Sell)
                        # Revert old action first, then apply new.
                        # Actually, Shadow Portfolio stores Net Position.
                        # If we bought 1000, now we want to Sell 500.
                        # The new card says "Sell 500".
                        # But wait, DecisionRecord is a "daily instruction".
                        # If morning says "Buy 1000" (Executed), and afternoon says "Sell 500" (New Instruction).
                        # Then afternoon record should replace morning record?
                        # If we replace, the record becomes "Sell 500".
                        # The net effect on shadow should be: Revert Buy 1000 (Sell 1000), then Execute Sell 500?
                        # That implies the user changed mind completely.
                        # YES, "Delete old strategy, use new one".
                        
                        # Revert Old
                        revert_action = "sell" if record_to_update.action.lower() == "buy" else "buy"
                        if old_qty > 0:
                            shadow_requests.append({
                                "symbol": symbol,
                                "action": revert_action,
                                "quantity": old_qty,
                                "price": exec_price # Use current price for revert? Or old price? Ideally current.
                            })
                        
                        # Apply New
                        delta_qty = new_qty
                        trade_action = action_str

                    record_to_update.action = action_str
                    record_to_update.price_at_suggestion = exec_price
                    record_to_update.suggested_quantity = new_qty
                    record_to_update.reasoning = f"{card.title}: {card.description}"
                    record_to_update.created_at = datetime.datetime.utcnow()
                    session.add(record_to_update)
                    logger.info(f"[Repository] Updated decision for {symbol}, delta={delta_qty} {trade_action}")

                else:
                    # --- Create new ---
                    delta_qty = new_qty
                    trade_action = action_str
                    
                    record = DecisionRecord(
                        user_id=user_id,
                        symbol=symbol,
                        action=action_str,
                        price_at_suggestion=exec_price,
                        suggested_quantity=new_qty,
                        reasoning=f"{card.title}: {card.description}",
                        status="active"
                    )
                    session.add(record)

                if delta_qty > 0:
                     shadow_requests.append({
                        "symbol": symbol,
                        "action": trade_action,
                        "quantity": delta_qty,
                        "price": exec_price
                    })
            
            session.commit()
            return shadow_requests

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

    def execute_shadow_trade(self, user_id: str, symbol: str, action: str, quantity: float, price: float) -> None:
        """
        Execute a trade on the Shadow Portfolio.
        """
        with Session(self.engine) as session:
            # 1. Get Shadow Portfolio
            shadow = session.exec(select(ShadowPortfolio).where(ShadowPortfolio.user_id == user_id)).first()
            if not shadow:
                # Try to create one if not exists (lazy init)
                logger.info(f"Shadow Portfolio not found for user {user_id}, initializing...")
                # We need initial cash balance, maybe fetch from real portfolio?
                # For safety, let's fetch real portfolio
                real_portfolio = session.exec(select(Portfolio).where(Portfolio.user_id == user_id)).first()
                initial_cash = real_portfolio.cash_balance if real_portfolio else 0.0
                
                shadow = ShadowPortfolio(user_id=user_id, cash_balance=initial_cash)
                session.add(shadow)
                session.commit()
                session.refresh(shadow)

            total_value = quantity * price
            logger.info(f"[ShadowTrade] {action} {symbol}: qty={quantity}, price={price}, total={total_value}")

            if action.upper() == "BUY":
                # Check Cash
                # if shadow.cash_balance < total_value:
                #    logger.warning(f"Insufficient cash for shadow trade: need {total_value}, have {shadow.cash_balance}")
                #    # We might allow negative cash (leverage) or partial fill, but for now let's just allow it (soft constraint) 
                #    # or log warning. Let's proceed to track performance even if cash goes negative? 
                #    # Better to just update it.
                
                # Update Cash
                shadow.cash_balance -= total_value
                
                # Find or Create Asset
                asset = session.exec(
                    select(ShadowAsset)
                    .where(ShadowAsset.portfolio_id == shadow.id)
                    .where(ShadowAsset.symbol == symbol)
                ).first()
                
                if asset:
                    # Update Avg Cost
                    current_total_cost = asset.quantity * asset.avg_cost
                    new_quantity = asset.quantity + quantity
                    
                    if new_quantity > 0:
                        asset.avg_cost = (current_total_cost + total_value) / new_quantity
                    
                    asset.quantity = new_quantity
                    session.add(asset)
                else:
                    asset = ShadowAsset(
                        portfolio_id=shadow.id,
                        symbol=symbol,
                        quantity=quantity,
                        avg_cost=price
                    )
                    session.add(asset)
                    
            elif action.upper() == "SELL":
                # Find Asset
                asset = session.exec(
                    select(ShadowAsset)
                    .where(ShadowAsset.portfolio_id == shadow.id)
                    .where(ShadowAsset.symbol == symbol)
                ).first()
                
                if not asset:
                    logger.warning(f"Asset {symbol} not found in shadow portfolio, cannot sell.")
                    return
                    
                # Update Cash
                shadow.cash_balance += total_value
                
                # Update Quantity
                if asset.quantity < quantity:
                     # Sell all
                     logger.warning(f"Selling all {symbol} (requested {quantity}, have {asset.quantity})")
                     quantity = asset.quantity
                
                asset.quantity -= quantity
                if asset.quantity <= 0:
                    session.delete(asset)
                else:
                    session.add(asset)
                
            shadow.updated_at = datetime.datetime.utcnow()
            session.add(shadow)
            session.commit()

