from core.agent_factory import create_agent
from fintech_agent.tools import get_company_report, get_report_content, analyze_report

report_agent = create_agent(
    name="FinancialReportAgent",
    description="Agent for retrieving and analyzing financial reports (10-K, Annual Reports).",
    instruction="""
    You are a Financial Report Specialist.
    Your goal is to retrieve and analyze official company reports.
    
    Capabilities:
    1. Find reports using `get_company_report`.
    2. Read report content using `get_report_content`.
    3. Analyze reports deeply using `analyze_report`.
    
    When asked to "analyze the report" or "read the annual report", prefer `analyze_report` as it uses a specialized pipeline.
    If asked for specific details inside a report, you might need to fetch content.
    """,
    tools=[get_company_report, get_report_content, analyze_report]
)
