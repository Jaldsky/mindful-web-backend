from typing import Any, Literal, TypeAlias

Password: TypeAlias = str
PasswordHash: TypeAlias = str

AccessToken: TypeAlias = str
RefreshToken: TypeAlias = str
TokenPayload: TypeAlias = dict[str, Any]

SessionStatus: TypeAlias = Literal["authenticated", "anonymous", "none"]
