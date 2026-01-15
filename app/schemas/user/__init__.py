from .profile import (
    ProfileResponseSchema,
    ProfileMethodNotAllowedSchema,
    ProfileUnauthorizedSchema,
    ProfileInternalServerErrorSchema,
)
from .profile_username import (
    UpdateUsernameRequestSchema,
    UpdateUsernameBadRequestSchema,
    UpdateUsernameConflictSchema,
    UpdateUsernameUnprocessableEntitySchema,
    UpdateUsernameMethodNotAllowedSchema,
    UpdateUsernameUnauthorizedSchema,
    UpdateUsernameInternalServerErrorSchema,
)
from .profile_email import (
    UpdateEmailRequestSchema,
    UpdateEmailBadRequestSchema,
    UpdateEmailConflictSchema,
    UpdateEmailUnprocessableEntitySchema,
    UpdateEmailMethodNotAllowedSchema,
    UpdateEmailUnauthorizedSchema,
    UpdateEmailInternalServerErrorSchema,
)

__all__ = (
    # Profile
    "ProfileResponseSchema",
    "ProfileMethodNotAllowedSchema",
    "ProfileUnauthorizedSchema",
    "ProfileInternalServerErrorSchema",
    # Update username
    "UpdateUsernameRequestSchema",
    "UpdateUsernameBadRequestSchema",
    "UpdateUsernameConflictSchema",
    "UpdateUsernameUnprocessableEntitySchema",
    "UpdateUsernameMethodNotAllowedSchema",
    "UpdateUsernameUnauthorizedSchema",
    "UpdateUsernameInternalServerErrorSchema",
    # Update email
    "UpdateEmailRequestSchema",
    "UpdateEmailBadRequestSchema",
    "UpdateEmailConflictSchema",
    "UpdateEmailUnprocessableEntitySchema",
    "UpdateEmailMethodNotAllowedSchema",
    "UpdateEmailUnauthorizedSchema",
    "UpdateEmailInternalServerErrorSchema",
)
