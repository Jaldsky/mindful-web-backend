from pydantic import BaseModel, Field


class ResendCodeResponseSchema(BaseModel):
    """Схема ответа на повторную отправку кода."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(default="Verification code sent successfully", description="Сообщение")
