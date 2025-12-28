from sqlmodel import create_engine, SQLModel, Session
import os
# Import models to ensure they are registered with SQLModel.metadata
from backend.infrastructure.database.models.research import ResearchJob, ResearchEvent, ResearchArtifact

# Ensure data directory exists
DATA_DIR = os.path.join(os.getcwd(), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

SQLITE_FILE_NAME = "research.db"
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, SQLITE_FILE_NAME)}"

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def get_session_factory():
    return Session(engine)
