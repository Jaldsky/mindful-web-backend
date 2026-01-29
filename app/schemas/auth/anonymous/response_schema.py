from pydantic import BaseModel, Field


class AnonymousResponseSchema(BaseModel):
    """Схема ответа на создание анонимной сессии."""

    code: str = Field(default="CREATED", description="Код ответа")
    message: str = Field(default="Anonymous session created", description="Сообщение")
    anon_id: str = Field(..., description="Идентификатор анонимного пользователя")
