"""
OMU-UBYS Custom Exceptions

This module contains all custom exceptions used by the omu-ubys library.
"""


class UBYSError(Exception):
    """Base exception for all UBYS-related errors."""
    pass


class LoginError(UBYSError):
    """
    Raised when login fails.
    
    Common causes:
        - Invalid username or password
        - Account locked
        - UBYS service unavailable
    """
    pass


class SessionExpiredError(UBYSError):
    """
    Raised when the session has expired.
    
    The UBYS session typically expires after 20-30 minutes of inactivity.
    You need to call `client.login()` again to refresh the session.
    """
    pass


class CSRFTokenError(UBYSError):
    """
    Raised when CSRF token cannot be obtained.
    
    This usually indicates that the UBYS homepage structure has changed
    or the service is temporarily unavailable.
    """
    pass


class ParseError(UBYSError):
    """
    Raised when HTML/JSON parsing fails.
    
    This may occur when:
        - UBYS page structure has changed
        - Unexpected response format
        - Session has expired (login page returned instead of data)
    """
    pass


class NetworkError(UBYSError):
    """
    Raised when a network-related error occurs.
    
    This includes connection timeouts, DNS failures, and SSL errors.
    """
    pass
