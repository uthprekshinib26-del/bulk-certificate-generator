from pydantic import BaseModel, EmailStr
from typing import List


class Student(BaseModel):
    name: str
    email: EmailStr


class BulkJobRequest(BaseModel):
    students: List[Student]