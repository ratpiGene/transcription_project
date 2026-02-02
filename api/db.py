import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from api.settings import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    input_path = Column(String, nullable=False)
    input_type = Column(String, nullable=False)
    output_type = Column(String, nullable=True)
    output_path = Column(String, nullable=True)
    result_text = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    error = Column(Text, nullable=True)
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=True)


class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


def create_job(job_id: str, filename: str, input_path: str, input_type: str) -> None:
    with SessionLocal() as session:
        job = Job(
            id=job_id,
            filename=filename,
            input_path=input_path,
            input_type=input_type,
            status="PENDING",
            created_at=_now(),
            updated_at=_now(),
        )
        session.add(job)
        session.commit()


def update_job(job_id: str, **fields: Any) -> None:
    if not fields:
        return
    with SessionLocal() as session:
        fields["updated_at"] = _now()
        session.query(Job).filter(Job.id == job_id).update(fields)
        session.commit()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        return job_to_dict(job) if job else None


def list_jobs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    output_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        query = session.query(Job).order_by(Job.created_at.desc())
        if status:
            query = query.filter(Job.status == status)
        if output_type:
            query = query.filter(Job.output_type == output_type)
        jobs = query.offset(offset).limit(limit).all()
        return [job_to_dict(job) for job in jobs]


def add_event(job_id: str, event: str) -> None:
    with SessionLocal() as session:
        session.add(JobEvent(job_id=job_id, event=event, created_at=_now()))
        session.commit()


def list_events(job_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        events = (
            session.query(JobEvent)
            .filter(JobEvent.job_id == job_id)
            .order_by(JobEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        return [event_to_dict(event) for event in events]


def get_metrics() -> Dict[str, Any]:
    with SessionLocal() as session:
        total_jobs = session.query(func.count(Job.id)).scalar() or 0
        avg_duration = (
            session.query(func.avg(Job.duration_seconds))
            .filter(Job.duration_seconds.isnot(None))
            .scalar()
            or 0.0
        )
        by_type = session.query(Job.output_type, func.count(Job.id)).group_by(Job.output_type).all()
        by_status = session.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
        failed_by_type = (
            session.query(Job.output_type, func.count(Job.id))
            .filter(Job.status == "FAILED")
            .group_by(Job.output_type)
            .all()
        )
        pending_by_type = (
            session.query(Job.output_type, func.count(Job.id))
            .filter(Job.status.in_(["PENDING", "QUEUED", "RUNNING"]))
            .group_by(Job.output_type)
            .all()
        )
        recent = session.query(Job).order_by(Job.created_at.desc()).limit(20).all()

    return {
        "total_jobs": total_jobs,
        "average_duration_seconds": float(avg_duration),
        "by_type": {row[0] or "unknown": row[1] for row in by_type},
        "by_status": {row[0]: row[1] for row in by_status},
        "failed_by_type": {row[0] or "unknown": row[1] for row in failed_by_type},
        "pending_by_type": {row[0] or "unknown": row[1] for row in pending_by_type},
        "pending_total": sum(row[1] for row in pending_by_type),
        "failed_total": sum(row[1] for row in failed_by_type),
        "recent_responses": [job_to_dict(job) for job in recent],
    }


def job_to_dict(job: Job) -> Dict[str, Any]:
    return {
        "id": job.id,
        "filename": job.filename,
        "input_path": job.input_path,
        "input_type": job.input_type,
        "output_type": job.output_type,
        "output_path": job.output_path,
        "result_text": job.result_text,
        "status": job.status,
        "error": job.error,
        "model_name": job.model_name,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "duration_seconds": job.duration_seconds,
    }


def event_to_dict(event: JobEvent) -> Dict[str, Any]:
    return {
        "id": event.id,
        "job_id": event.job_id,
        "event": event.event,
        "created_at": event.created_at.isoformat(),
    }
