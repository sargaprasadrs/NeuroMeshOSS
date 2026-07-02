from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    password_hash: str
    is_active: bool = True
    role: str = "user"

    class Config:
        frozen = True
