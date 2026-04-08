class DomainError(Exception):
    pass


class ValidationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class DuplicateError(DomainError):
    pass


class AuthError(DomainError):
    pass


class PermissionDenied(DomainError):
    pass
