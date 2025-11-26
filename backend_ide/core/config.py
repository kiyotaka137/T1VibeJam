from pathlib import Path
import os

# JWT
SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_ME"
ALGORITHM = "HS256"

# Docker runner
LANGUAGE_RUNNERS = {
    "py": "python-runner",
    "js": "js-runner",
    "cpp": "cpp-runner",
}

# Job dir
JOB_BASE_DIR = "/tmp/jobs"
Path(JOB_BASE_DIR).mkdir(parents=True, exist_ok=True)

# DATABASE
# Для разработки можешь захардкодить, потом вынесешь в env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:mypassword@localhost:5432/interview_service",
)
