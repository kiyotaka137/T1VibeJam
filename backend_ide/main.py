from fastapi import FastAPI

from backend_ide.api.routes import users, submissions

app = FastAPI(title="Online Interview Backend")

# Подключаем роутеры
app.include_router(users.router)
app.include_router(submissions.router)
