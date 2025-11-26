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
from backend_ide.services.docker_runner import run_in_docker, normalize_language
from backend_ide.services.stats_events import (
    build_attempt_event,
    build_task_completed_event,
    send_events,
)
from backend_ide.services.tests_getter import fetch_tests_from_rag

router = APIRouter()

@router.post("/submit", response_model=SubmissionResponse)
async def submit_solution(
    payload: SubmissionRequest,

):
    """
    Приём решения:
    - JWT уже проверен через Depends(get_current_user)
    - Проверен дедлайн
    - Создаём временную директорию
    - Пишем туда solution.* и тесты
    - Запускаем Docker-контейнер с тестами
    - Возвращаем количество пройденных тестов и детали
    """

    test_cases = await fetch_tests_from_rag(payload.task_id)
    #test_cases = await get_test_cases_for_task(str(payload.task_id))

    if not test_cases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тесты для задачи {payload.task_id} не найдены",
        )

    job_dir = tempfile.mkdtemp(
        prefix=f"user_{payload.task_id}_",
        dir=JOB_BASE_DIR,
    )

    lang = normalize_language(payload.language)

    if lang == "py":
        solution_filename = "solution.py"
    elif lang == "js":
        solution_filename = "solution.js"
    elif lang == "cpp":
        solution_filename = "solution.cpp"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Язык {payload.language!r} не поддерживается",
        )

    try:
        if lang == "js":
            if "module.exports" not in payload.source_code:

                payload.source_code += """
                // --- автодобавлено платформой ---
                if (typeof module !== "undefined" && module.exports) {
                    if (typeof main !== "undefined") {
                        module.exports.main = main;
                    }
                }
                """
        # solution.*
        solution_path = Path(job_dir) / solution_filename
        solution_path.write_text(payload.source_code, encoding="utf-8")

        # cases.json – просто дамп того, что было в БД
        cases_path = Path(job_dir) / "cases.json"
        cases_path.write_text(
            json.dumps(test_cases, ensure_ascii=False),
            encoding="utf-8",
        )

        raw_result = run_in_docker(job_dir, payload.language, len(test_cases))

        # Ожидаем формат:
        # {
        #   "testsRun": int,
        #   "failures": int,
        #   "errors": int,
        #   "skipped": int,
        #   "passed": int,
        #   "failure_details": [{"test": "...", "traceback": "..."}]
        # }


        # tests_total = int(raw_result.get("testsRun", 0))
        # failures = int(raw_result.get("failures", 0))
        # errors = int(raw_result.get("errors", 0))
        # skipped = int(raw_result.get("skipped", 0))
        # passed = int(
        #     raw_result.get(
        #         "passed",
        #         tests_total - failures - errors - skipped,
        #     )
        # )

        # total = raw_result.get("testsRun", 0)
        # passed = raw_result.get("passed", 0)
        # failed = total - passed

        # first_idx = raw_result.get("first_failed_index")
        # first_type = raw_result.get("first_failed_type")

        # if first_idx is not None:
        #     first_number = first_idx + 1  # из 0-based делаем 1-based
        # else:
        #     first_number = None

        
                
        # return SubmissionResponse(
        #     total_tests=total,
        #     passed_tests=passed,
        #     failed_tests=failed,
        #     all_passed=(failed == 0),
        #     first_failed_test_number=first_number,
        #     first_failed_type=first_type,
        # )

        tests_run = raw_result.get("testsRun", 0) or 0
        failures = raw_result.get("failures", 0) or 0
        errors = raw_result.get("errors", 0) or 0
        passed = raw_result.get("passed", 0) or 0
        first_failed_index = raw_result.get("first_failed_index")
        first_failed_type = raw_result.get("first_failed_type")
        first_failed_id = raw_result.get("first_failed_id")

        all_passed = (tests_run > 0 and failures == 0 and errors == 0)

        response = SubmissionResponse(
            total_tests=tests_run,
            passed_tests=passed,
            failed_tests=failures,
            all_passed=all_passed,
            first_failed_test_number=(
                None if first_failed_index is None else first_failed_index + 1
            ),
        )

        # ==== События для interview-stats-svc ====
        # interview_id и candidate_user_id можно взять:
        # - из payload (если ты их туда кладёшь)
        # - или из current_user / контекста интервью
        interview_id = payload.interview_id
        candidate_user_id = payload.candidate_user_id

        events = []

        # 1) attempt — на КАЖДЫЙ запуск проверки (и run, и submit)
        attempt_event = build_attempt_event(
            interview_id=interview_id,
            candidate_user_id=candidate_user_id,
            task_id=payload.task_id,
            raw_result=raw_result,
            source="task",
        )
        events.append(attempt_event)

        # 2) task_completed — только если это submit И все тесты прошли
        if payload.mode == "submit" and all_passed:
            completed_event = build_task_completed_event(
                interview_id=interview_id,
                candidate_user_id=candidate_user_id,
                task_id=payload.task_id,
                reason="solved",
                source="task",
            )
            events.append(completed_event)

        # отправляем батч
        await send_events(events)

        return response

    finally:
        shutil.rmtree(job_dir, ignore_errors=True)
