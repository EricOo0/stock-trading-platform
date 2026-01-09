from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ResearchSignal(BaseModel):
    condition: str = Field(
        ..., description="The condition observed (e.g. 'High Volume + Net Inflow')")
    result: str = Field(...,
                        description="The implication or signal (e.g. 'Buy Signal')")


class ResearchOutlook(BaseModel):
    score: int = Field(..., description="Sentiment score from 0 (Extreme Caution) to 100 (Extreme Optimism)")
    label: Literal['Extreme Caution', 'Caution', 'Neutral', 'Optimism',
                   'Extreme Optimism'] = Field(..., description="Textual label for the outlook")


class ResearchReference(BaseModel):
    id: str = Field(..., description="Unique identifier for the reference")
    title: str = Field(..., description="Title of the article or source")
    source: str = Field(...,
                        description="Name of the source (e.g. 'Bloomberg', 'MarketWire')")
    url: Optional[str] = Field(
        None, description="URL to the source if available")


class DeepResearchReport(BaseModel):
    """
    Structured output for the Deep Research Agent's final report.
    """
    signals: List[ResearchSignal] = Field(...,
                                          description="Key market signals identified")
    analysis: str = Field(...,
                          description="Detailed trend analysis and summary text")
    outlook: ResearchOutlook = Field(...,
                                     description="Overall market outlook assessment")
    references: List[ResearchReference] = Field(
        ..., description="List of sources used for the analysis")
