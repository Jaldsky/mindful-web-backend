from .request_schema import UpdateEmailRequestSchema
from .bad_request_schema import UpdateEmailBadRequestSchema
from .conflict_schema import UpdateEmailConflictSchema
from .unprocessable_entity_schema import UpdateEmailUnprocessableEntitySchema
from .method_not_allowed_schema import UpdateEmailMethodNotAllowedSchema
from .unauthorized_schema import UpdateEmailUnauthorizedSchema
from .internal_server_error_schema import UpdateEmailInternalServerErrorSchema

__all__ = (
    "UpdateEmailRequestSchema",
    "UpdateEmailBadRequestSchema",
    "UpdateEmailConflictSchema",
    "UpdateEmailUnprocessableEntitySchema",
    "UpdateEmailMethodNotAllowedSchema",
    "UpdateEmailUnauthorizedSchema",
    "UpdateEmailInternalServerErrorSchema",
)
