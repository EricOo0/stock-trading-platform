from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, List, AsyncGenerator
import json
import logging
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from sqlmodel import select, Session

from backend.app.agents.personal_finance.models import (
    AssetItem,
    PriceUpdateMap,
    PriceUpdate,
    PortfolioSnapshot,
)
from backend.app.services.personal_finance_service import (
    update_prices,
    get_portfolio,
    save_portfolio,
)
from backend.app.agents.personal_finance.agent import create_personal_finance_graph
from backend.app.agents.personal_finance.db import engine
from backend.app.agents.personal_finance.db_models import PerformanceHistory
from backend.app.agents.personal_finance.performance_service import ensure_performance_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/personal-finance", tags=["Personal Finance"])


class UpdatePricesRequest(BaseModel):
    assets: List[AssetItem]


class PerformanceDataPoint(BaseModel):
    date: str
    nav_user: float
    nav_ai: float
    nav_sh: float
    nav_sz: float

class PerformanceResponse(BaseModel):
    start_date: str
    series: List[PerformanceDataPoint]


@router.get("/portfolio", response_model=PortfolioSnapshot)
async def get_user_portfolio(user_id: str = "default_user"):
    """
    Get user portfolio.
    """
    try:
        return await get_portfolio(user_id)
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio", response_model=PortfolioSnapshot)
async def save_user_portfolio(
    snapshot: PortfolioSnapshot, user_id: str = "default_user"
):
    """
    Save user portfolio.
    """
    try:
        return await save_portfolio(user_id, snapshot)
    except Exception as e:
        logger.error(f"Error saving portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-prices", response_model=PriceUpdateMap)
async def update_asset_prices(request: UpdatePricesRequest):
    """
    Batch update asset prices.
    Currently supports:
    - Stock (via Sina)
    - Fund (via AkShare)
    Other types will be ignored in the update but original data structure is preserved by frontend.
    """
    try:
        updated_prices = await update_prices(request.assets)
        return updated_prices
    except Exception as e:
        logger.error(f"Error updating prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=PerformanceResponse)
async def get_performance_history(user_id: str = "default_user"):
    with Session(engine) as session:
        # 1. Ensure history is up to date (Lazy Backfill)
        await ensure_performance_history(user_id, session)

        # 2. Fetch all history
        stmt = select(PerformanceHistory).where(PerformanceHistory.user_id == user_id).order_by(PerformanceHistory.date)
        history = session.exec(stmt).all()

        if not history:
            return PerformanceResponse(start_date="", series=[])

        series = []
        for h in history:
            series.append(PerformanceDataPoint(
                date=h.date,
                nav_user=h.nav_user,
                nav_ai=h.nav_ai,
                nav_sh=h.nav_sh,
                nav_sz=h.nav_sz
            ))

        return PerformanceResponse(
            start_date=history[0].date,
            series=series
        )


async def stream_analysis(portfolio: PortfolioSnapshot) -> AsyncGenerator[str, None]:
    """
    Streams analysis updates and final report.
    """
    graph = create_personal_finance_graph()

    # Initial State
    user_query = portfolio.query or "请分析我的投资组合并给出建议。"
    initial_state = {
        "messages": [HumanMessage(content=user_query)],
        "portfolio": portfolio.dict(),
        "user_id": "default_user",  # TODO: Get from auth
        "session_id": "default_session",
    }

    yield json.dumps(
        {"type": "status", "content": "Analyzing portfolio context..."}
    ) + "\n"

    try:
        async for event in graph.astream(initial_state):
            # event is a dict of {node_name: state_update}
            for node, update in event.items():
                if node == "pre_process":
                    replay_enabled = update.get("replay_enabled")
                    lessons_count = update.get("lessons_count")
                    yield json.dumps(
                        {
                            "type": "status",
                            "content": f"PreProcess 完成：replay={replay_enabled}, lessons={lessons_count}",
                        }
                    ) + "\n"
                if node == "planner":
                    agents = update.get("selected_agents", [])
                    yield json.dumps(
                        {
                            "type": "status",
                            "content": f"计划生成完成：{', '.join(agents)}",
                        }
                    ) + "\n"
                elif node == "executor":
                    if isinstance(update, dict) and update.get("status"):
                        yield json.dumps(
                            {"type": "status", "content": update.get("status")}
                        ) + "\n"
                    elif isinstance(update, dict) and update.get("task_update"):
                        tu = update.get("task_update")
                        if isinstance(tu, dict):
                            # Send detailed task result as a step
                            yield json.dumps(
                                {
                                    "type": "step",
                                    "step_type": "task_result",
                                    "title": tu.get('title'),
                                    "status": tu.get('status'),
                                    "content": tu.get('result', '')  # Forward the result content
                                }
                            ) + "\n"
                    else:
                        yield json.dumps(
                            {"type": "status", "content": "子任务执行完成。"}
                        ) + "\n"
                elif node == "synthesizer":
                    # Stream final report tokens?
                    # LangGraph astream returns state updates, not tokens.
                    # To stream tokens, we'd need to hook into the LLM callback within the node or use astream_events.
                    # For now, we send the full report at the end.

                    report = update.get("final_report", "")
                    yield json.dumps({"type": "report_chunk", "content": report}) + "\n"

                    cards = update.get("recommendation_cards", [])
                    for card in cards:
                        # card is already a dict since orchestrator serialized it
                        card_data = card if isinstance(card, dict) else card.dict()
                        yield json.dumps({"type": "card", "data": card_data}) + "\n"

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    yield json.dumps({"type": "done", "content": "Analysis complete"}) + "\n"


@router.post("/analyze")
async def analyze_portfolio(request: PortfolioSnapshot):
    """
    Analyze portfolio using AI agents (Streaming).
    """
    return StreamingResponse(
        stream_analysis(request), media_type="application/x-ndjson"
    )
