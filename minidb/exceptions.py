class DBError(Exception):
    """Base class for exceptions in MiniDB."""
    pass

class TableNotFoundError(DBError):
    """Raised when a table cannot be found."""
    pass

class ValidationError(DBError):
    """Raised when data validation fails."""
    pass

class DuplicateKeyError(ValidationError):
    """Raised when a primary key constraint is violated."""
    pass

class UniqueConstraintError(ValidationError):
    """Raised when a unique constraint is violated."""
    pass

class DatabaseBusyError(DBError):
    """Raised when a lock cannot be acquired within timeout period."""
    pass

class SchemaError(DBError):
    """Raised when a schema modification violates constraints."""
    pass
