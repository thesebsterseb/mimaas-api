"""
MIMaaS API Client Exceptions

Comprehensive error hierarchy for handling all error conditions in the MIMaaS API client.
"""


class MIMaaSError(Exception):
    """Base exception for all MIMaaS errors"""
    pass


class NetworkError(MIMaaSError):
    """Network communication errors (connection timeouts, DNS failures, etc.)"""
    pass


class AuthenticationError(MIMaaSError):
    """Authentication/authorization errors (invalid token, missing token, etc.)"""
    pass


class QuotaExceededError(MIMaaSError):
    """User quota exceeded (no available runs remaining)"""

    def __init__(self, available_runs=0, message=None):
        self.available_runs = available_runs
        if message is None:
            message = f"No available runs remaining. Available: {available_runs}"
        super().__init__(message)


class ValidationError(MIMaaSError):
    """
    Model validation errors (invalid file format, unsupported operators, model too large, etc.)
    """
    pass


class ProcessingError(MIMaaSError):
    """Request processing errors (flash failures, compilation errors, etc.)"""

    def __init__(self, stage=None, message=None):
        self.stage = stage  # e.g., "flash", "precheck", "evaluation"
        self.message = message
        error_msg = f"Processing failed"
        if stage:
            error_msg += f" at stage '{stage}'"
        if message:
            error_msg += f": {message}"
        super().__init__(error_msg)


class ResourceNotFoundError(MIMaaSError):
    """Requested resource not found (request ID, board name, etc.)"""
    pass


class BoardNotAvailableError(MIMaaSError):
    """Requested board not available or not found"""
    pass


class TimeoutError(MIMaaSError):
    """Operation timed out (request processing, polling, etc.)"""
    pass


class ConfigurationError(MIMaaSError):
    """Configuration errors (missing config file, invalid config values, etc.)"""
    pass
