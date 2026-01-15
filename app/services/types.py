from typing import TypeAlias, Literal
from uuid import UUID

UserId: TypeAlias = UUID
Username: TypeAlias = str
Email: TypeAlias = str
VerificationCode: TypeAlias = str
ActorType: TypeAlias = Literal["access", "anon"]
