class EnvifrogError(Exception):
    """Base exception for all envifrog errors."""
    pass


class MissingVariableError(EnvifrogError):
    """Raised when a required environment variable is missing."""
    pass


class ValidationError(EnvifrogError):
    """Raised when a variable fails validation (e.g. min/max constraints)."""
    pass


class TypeCastingError(EnvifrogError):
    """Raised when a variable cannot be cast to the specified type."""
    pass
