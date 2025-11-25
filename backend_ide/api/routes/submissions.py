import shutil
import tempfile
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from backend_ide.api.deps import get_current_user
from backend_ide.core.config import JOB_BASE_DIR
from backend_ide.schemas.user import User
from backend_ide.schemas.submission import (
    SubmissionRequest,
    SubmissionResponse,
    FailedTest,
)
from backend_ide.services.task_service import get_test_cases_for_task
from backend_ide.services.docker_runner import run_in_docker

router = APIRouter()


# @router.post("/submit", response_model=SubmissionResponse)
# async def submit_solution(
#     payload: SubmissionRequest,
#     user: User = Depends(get_current_user),
# ):

@router.post("/submit", response_model=SubmissionResponse)
async def submit_solution(
    payload: SubmissionRequest,

):
    """
    Приём решения:
    - JWT уже проверен через Depends(get_current_user)
    - Проверен дедлайн
    - Создаём временную директорию
    - Пишем туда solution.py и тесты
    - Запускаем Docker-контейнер с тестами
    - Возвращаем количество пройденных тестов и детали
    """

    if payload.language.lower() != "python":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сейчас поддерживается только Python",
        )
    
    test_cases = await get_test_cases_for_task(str(payload.task_id))

    if not test_cases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тесты для задачи {payload.task_id} не найдены",
        )

    job_dir = tempfile.mkdtemp(
        prefix=f"user_{payload.task_id}_",
        dir=JOB_BASE_DIR,
    )

    try:
        # solution.py
        solution_path = Path(job_dir) / "solution.py"
        solution_path.write_text(payload.source_code, encoding="utf-8")

        # cases.json – просто дамп того, что было в БД
        cases_path = Path(job_dir) / "cases.json"
        cases_path.write_text(
            json.dumps(test_cases, ensure_ascii=False),
            encoding="utf-8",
        )

        raw_result = run_in_docker(job_dir)

        # Ожидаем формат:
        # {
        #   "testsRun": int,
        #   "failures": int,
        #   "errors": int,
        #   "skipped": int,
        #   "passed": int,
        #   "failure_details": [{"test": "...", "traceback": "..."}]
        # }
        tests_total = int(raw_result.get("testsRun", 0))
        failures = int(raw_result.get("failures", 0))
        errors = int(raw_result.get("errors", 0))
        skipped = int(raw_result.get("skipped", 0))
        passed = int(
            raw_result.get(
                "passed",
                tests_total - failures - errors - skipped,
            )
        )

        failure_details_raw = raw_result.get("failure_details", []) or []
        failure_details = [
            FailedTest(test=item.get("test", ""), traceback=item.get("traceback", ""))
            for item in failure_details_raw
        ]

        return SubmissionResponse(
            tests_total=tests_total,
            tests_passed=passed,
            tests_failed=failures,
            tests_with_errors=errors,
            failed_details=failure_details,
        )

    finally:
        shutil.rmtree(job_dir, ignore_errors=True)
