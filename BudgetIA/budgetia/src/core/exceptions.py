class BudgetException(Exception):
    """Base exception for all BudgetIA errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class APIConnectionError(BudgetException):
    """Raised when the API is unreachable (ConnectionError, Timeout, etc)."""
    pass

class APIResponseError(BudgetException):
    """Raised when the API returns an error status code (4xx, 5xx)."""
    def __init__(self, status_code: int, message: str):
        super().__init__(f"API Error {status_code}: {message}")
        self.status_code = status_code

class AuthenticationError(APIResponseError):
    """Raised when authentication fails (401/403)."""
    pass

class NotFoundError(APIResponseError):
    """Raised when a resource is not found (404)."""
    pass

class ServerError(APIResponseError):
    """Raised when the server encounters an error (500+)."""
    pass
