from typing import Any, TypeAlias

Password: TypeAlias = str
PasswordHash: TypeAlias = str

AccessToken: TypeAlias = str
RefreshToken: TypeAlias = str
TokenPayload: TypeAlias = dict[str, Any]
