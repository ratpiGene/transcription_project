from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class RunRequest(BaseModel):
    output_type: str
    model_name: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    status: str
    output_type: Optional[str] = None
    output_path: Optional[str] = None
    result_text: Optional[str] = None
    error: Optional[str] = None


class JobItem(BaseModel):
    id: str
    filename: str
    input_type: str
    output_type: Optional[str]
    status: str
    created_at: str
    updated_at: str
    duration_seconds: Optional[float]


class JobListResponse(BaseModel):
    items: List[JobItem]
    total: int


class MetricsResponse(BaseModel):
    total_jobs: int
    average_duration_seconds: float
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    failed_by_type: Dict[str, int]
    pending_by_type: Dict[str, int]
    pending_total: int
    failed_total: int
    recent_responses: List[Dict[str, Any]]
