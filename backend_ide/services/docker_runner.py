import json
import subprocess

from fastapi import HTTPException, status

from backend_ide.core.config import LANGUAGE_RUNNERS

def normalize_language(lang: str) -> str:
    lang = (lang or "").strip().lower()
    if lang == "python":
        return "py"
    if lang == "javascript":
        return "js"
    if lang == "c++":
        return "cpp"
    return lang

def compute_docker_timeout(tests_count: int) -> int:
    base_overhead = 1.0       # сек
    per_test_limit = 2.0      # сек на тест (синхронизируй с раннерами)
    safety_factor = 1.3
    hard_cap = 60.0

    if tests_count <= 0:
        return 10  # дефолт, если вдруг что-то пошло не так

    timeout = base_overhead + per_test_limit * tests_count * safety_factor
    timeout = max(5.0, min(hard_cap, timeout))  # не меньше 5, не больше 60
    return int(timeout)

def run_in_docker(job_dir: str, language: str, tests_count: int) -> dict:
    """
    Запускает Docker-контейнер с образом RUNNER_IMAGE.
    Внутри контейнера должен быть скрипт run_tests.py, который:
    - принимает путь к job-директории (например, /backend_ide/job)
    - выводит JSON с результатами тестов в stdout
    """
    lang = normalize_language(language)
    image = LANGUAGE_RUNNERS.get(lang)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Язык {language!r} не поддерживается",
        )

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{job_dir}:/backend_ide/job",
        "--network=none",
        "--memory=256m",
        "--cpus=1",
        image,
        "/backend_ide/job",
    ]

    docker_timeout = compute_docker_timeout(tests_count)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=docker_timeout,
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
