from typing import Optional, Literal
from pydantic import BaseModel
from enum import Enum

class SubmissionRequest(BaseModel):
    task_id: str
    language: str = "python"
    source_code: str
    mode: Literal["run", "submit"] = "run"

    interview_id: str   # UUID интервью
    candidate_user_id: str  # UUID кандидата 


class FailedTest(BaseModel):
    test: int
    traceback: str

class SubmissionResponse(BaseModel):
    total_tests: int
    passed_tests: int
    failed_tests: int
    all_passed: bool

    first_failed_test_number: Optional[int] = None  # 1-based
