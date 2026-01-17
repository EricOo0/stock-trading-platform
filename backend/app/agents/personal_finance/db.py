import os
from sqlmodel import create_engine, SQLModel, Session
from backend.app.agents.personal_finance.db_models import Portfolio, Asset, DecisionRecord

# Define path relative to this agent
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(AGENT_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

SQLITE_FILE_NAME = "portfolio.db"
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, SQLITE_FILE_NAME)}"

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
