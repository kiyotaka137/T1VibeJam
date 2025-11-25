from typing import List
from pydantic import BaseModel


class SubmissionRequest(BaseModel):
    task_id: str
    language: str = "python"
    source_code: str


class FailedTest(BaseModel):
    test: int
    traceback: str


class SubmissionResponse(BaseModel):
    tests_total: int
    tests_passed: int
    tests_failed: int
    tests_with_errors: int
    failed_details: List[FailedTest] = []
    