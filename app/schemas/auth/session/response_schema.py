from pydantic import BaseModel, Field
from typing import Literal, Optional


class SessionResponseSchema(BaseModel):
    """Схема ответа на проверку текущей сессии."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(..., description="Сообщение")
    status: Literal["authenticated", "anonymous", "none"] = Field(..., description="Статус сессии")
    user_id: Optional[str] = Field(None, description="ID пользователя (если authenticated)")
    anon_id: Optional[str] = Field(None, description="ID анонимной сессии (если anonymous)")
