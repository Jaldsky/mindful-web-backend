from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

ExceptionMessage = str
DatabaseURL = str
DatabaseSession = Union[Session, AsyncSession]
