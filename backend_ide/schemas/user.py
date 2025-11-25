from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str
    assignment_deadline: datetime
