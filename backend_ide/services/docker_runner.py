import json
import subprocess

from fastapi import HTTPException, status

from backend_ide.core.config import RUNNER_IMAGE


def run_in_docker(job_dir: str) -> dict:
    """
    Запускает Docker-контейнер с образом RUNNER_IMAGE.
    Внутри контейнера должен быть скрипт run_tests.py, который:
    - принимает путь к job-директории (например, /backend_ide/job)
    - выводит JSON с результатами тестов в stdout
    """
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{job_dir}:/backend_ide/job",
        "--network=none",
        "--memory=256m",
        "--cpus=1",
        RUNNER_IMAGE,
        "/backend_ide/job",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Таймаут при выполнении решения в Docker",
        ) from e

    if proc.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при запуске контейнера: {proc.stderr.strip()}",
        )

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Невалидный JSON от тестового контейнера"
        ) from e
