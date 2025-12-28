from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from backend.infrastructure.database.models.research import (
    ResearchJob,
    ResearchEvent,
    ResearchArtifact,
)
from backend.infrastructure.database.engine import engine
from backend.infrastructure.adk.core.memory_client import MemoryClient
import asyncio
import logging

logger = logging.getLogger(__name__)


class JobManager:
    def __init__(self):
        self.engine = engine  # Use the singleton engine

    def _get_session(self):
        return Session(self.engine)

    def create_job(self, user_id: str, query: str) -> ResearchJob:
        with self._get_session() as session:
            job = ResearchJob(user_id=user_id, query=query, status="pending")
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def update_job_status(
        self, job_id: str, status: str, output: Optional[str] = None
    ) -> Optional[ResearchJob]:
        with self._get_session() as session:
            statement = select(ResearchJob).where(ResearchJob.id == job_id)
            job = session.exec(statement).first()
            if job:
                job.status = status
                job.updated_at = datetime.utcnow()
                session.add(job)
                session.commit()
                session.refresh(job)

                # Also log as event for history tracking
                payload = {"status": status}
                if output:
                    payload["output"] = output

                # Avoid duplicate event if caller already logged it (optional check, but safe to log status change)
                # For now we just log it as a system event
                self.append_event(job_id, "status_change", payload)

                # Trigger Memory Finalize if completed
                if status == "completed":
                    user_id = job.user_id or "default_user"
                    asyncio.create_task(self._finalize_memory(user_id))

                return job
            return None

    async def _finalize_memory(self, user_id: str):
        """异步调用记忆系统结算接口"""
        try:
            client = MemoryClient(user_id=user_id, agent_id="research_agent")
            success = client.finalize()
            if success:
                logger.info(f"Memory finalized for user {user_id}")
            else:
                logger.warning(f"Memory finalize failed for user {user_id}")
        except Exception as e:
            logger.error(f"Error during memory finalize: {e}")

    def append_event(
        self, job_id: str, event_type: str, payload: Dict[str, Any]
    ) -> ResearchEvent:
        with self._get_session() as session:
            event = ResearchEvent(
                job_id=job_id,
                type=event_type,
                payload=payload,
                timestamp=datetime.utcnow(),
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def create_artifact(
        self,
        job_id: str,
        artifact_type: str,
        data: Dict[str, Any],
        title: Optional[str] = None,
    ) -> ResearchArtifact:
        with self._get_session() as session:
            artifact = ResearchArtifact(
                job_id=job_id, type=artifact_type, data=data, title=title
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            return artifact

    def get_job(self, job_id: str) -> Optional[ResearchJob]:
        with self._get_session() as session:
            statement = select(ResearchJob).where(ResearchJob.id == job_id)
            return session.exec(statement).first()

    def get_job_with_events(self, job_id: str) -> Optional[ResearchJob]:
        with self._get_session() as session:
            # Assuming lazy loading or configured relationship; simple get for now
            # For deep fetch usually we utilize options(selectinload(ResearchJob.events))
            # But here just fetching simple job and later we can fetch events if needed or use SQLModel relations
            statement = select(ResearchJob).where(ResearchJob.id == job_id)
            job = session.exec(statement).first()
            return job

    def get_events(self, job_id: str) -> List[ResearchEvent]:
        with self._get_session() as session:
            statement = (
                select(ResearchEvent)
                .where(ResearchEvent.job_id == job_id)
                .order_by(ResearchEvent.timestamp)
            )
            return session.exec(statement).all()

    def get_artifacts(self, job_id: str) -> List[ResearchArtifact]:
        with self._get_session() as session:
            statement = (
                select(ResearchArtifact)
                .where(ResearchArtifact.job_id == job_id)
                .order_by(ResearchArtifact.created_at)
            )
            return session.exec(statement).all()

    def list_jobs(self, user_id: str, limit: int = 20) -> List[ResearchJob]:
        with self._get_session() as session:
            statement = (
                select(ResearchJob)
                .where(ResearchJob.user_id == user_id)
                .order_by(ResearchJob.created_at.desc())
                .limit(limit)
            )
            return session.exec(statement).all()
