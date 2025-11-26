import os
from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid

import httpx
from pydantic import BaseModel


STATS_SERVICE_URL = os.getenv(
    "INTERVIEW_STATS_URL",
    "http://interview-stats-svc:8000/internal/events",  # имя сервиса в докере
)

STATS_API_KEY = os.getenv("INTERVIEW_STATS_API_KEY", "secret-dev-key")


class StatsEvent(BaseModel):
    interview_id: str
    candidate_user_id: str
    task_id: str
    source: str  # "task|session|frontend|runner|any"
    type: str    # "task_assigned|attempt|task_completed|anti_cheat_violation|paste_blocked"
    ts: str      # RFC3339
    payload: Dict[str, Any]


def _now_rfc3339_utc() -> str:
    # 2025-11-26T00:08:00Z
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def send_events(events: List[StatsEvent]) -> None:
    """
    Отправка батча событий в interview-stats-svc.
    Ошибки логируем, но не ломаем основную бизнес-логику.
    """
    if not events:
        return

    if not STATS_SERVICE_URL:
        print("[stats] STATS_SERVICE_URL not set, skipping send_events")
        return

    payload = {
        "events": [e.model_dump() for e in events],
    }

    headers = {
        "Content-Type": "application/json",
        "X-Internal-API-Key": STATS_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(STATS_SERVICE_URL, json=payload, headers=headers)
        if resp.status_code >= 400:
            print(f"[stats] non-2xx response: {resp.status_code}, body={resp.text}")
    except Exception as e:
        print(f"[stats] failed to send events: {repr(e)}")

def build_attempt_event(
    *,
    interview_id: str,
    candidate_user_id: str,
    task_id: str,
    raw_result: dict,
    source: str = "task",
) -> StatsEvent:
    """
    Строим событие type=attempt из результата раннера.
    """

    tests_total = int(raw_result.get("testsRun", 0) or 0)
    failures = int(raw_result.get("failures", 0) or 0)
    errors = int(raw_result.get("errors", 0) or 0)
    passed = int(raw_result.get("passed", 0) or 0)
    first_failed_type = raw_result.get("first_failed_type")

    # compile_ok и result
    # очень грубая логика:
    # - если tests_total == 0 и errors > 0 → compile_error
    # - если tests_total > 0 и errors > 0 → runtime_error
    # - если errors == 0:
    #     - passed == tests_total → ok
    #     - passed < tests_total → tests_failed
    if errors > 0 and tests_total == 0:
        result = "compile_error"
        compile_ok = False
    elif errors > 0 and tests_total > 0:
        result = "runtime_error"
        compile_ok = False
    else:
        compile_ok = True
        if tests_total > 0 and passed == tests_total:
            result = "ok"
        elif tests_total > 0 and passed < tests_total:
            result = "tests_failed"
        else:
            # нет тестов / странный кейс
            result = "wrong"

    attempt_id = str(uuid.uuid4())

    event = StatsEvent(
        interview_id=interview_id,
        candidate_user_id=candidate_user_id,
        task_id=task_id,
        source=source,
        type="attempt",
        ts=_now_rfc3339_utc(),
        payload={
            "attempt_id": attempt_id,
            "result": result,
            "compile_ok": compile_ok,
            "tests_total": tests_total,
            "tests_passed": passed,
        },
    )
    return event

def build_task_completed_event(
    *,
    interview_id: str,
    candidate_user_id: str,
    task_id: str,
    reason: str = "solved",
    source: str = "task",
) -> StatsEvent:
    return StatsEvent(
        interview_id=interview_id,
        candidate_user_id=candidate_user_id,
        task_id=task_id,
        source=source,
        type="task_completed",
        ts=_now_rfc3339_utc(),
        payload={"reason": reason},
    )
