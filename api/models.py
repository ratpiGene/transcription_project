from pydantic import BaseModel
from typing import Optional


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
