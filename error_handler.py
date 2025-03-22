"""
Centralized error handling for GitHub Contribution Hack

Provides standardized error handling, custom exceptions,
and error categorization for the application.
"""
import sys
import traceback
import logging
from typing import Optional, Dict, Any, List, Type, Callable
from functools import wraps

# Configure logger
logger = logging.getLogger(__name__)

# Error categories
class ErrorCategory:
    """Categories for errors to aid in proper handling and reporting"""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    API = "api"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    INPUT_VALIDATION = "input_validation"
    TIMEOUT = "timeout"
    GIT = "git"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"

# Base custom exception
class ContributionError(Exception):
    """Base exception for all GitHub Contribution Hack errors"""
    
    def __init__(self, 
                message: str, 
                category: str = ErrorCategory.UNKNOWN,
                details: Optional[Dict[str, Any]] = None,
                recovery_hint: Optional[str] = None,
                original_exception: Optional[Exception] = None):
        """
        Initialize exception
        
        Args:
            message: Error message
            category: Error category from ErrorCategory
            details: Additional error details
            recovery_hint: Hint for recovering from the error
            original_exception: Original exception if this is a wrapper
        """
        self.message = message
        self.category = category
        self.details = details or {}
        self.recovery_hint = recovery_hint
        self.original_exception = original_exception
        
        # Format message with recovery hint if available
        full_message = message
        if recovery_hint:
            full_message = f"{message} - Recovery: {recovery_hint}"
            
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        result = {
            "error": self.__class__.__name__,
            "message": self.message,
            "category": self.category
        }
        
        if self.details:
            result["details"] = self.details
            
        if self.recovery_hint:
            result["recovery_hint"] = self.recovery_hint
            
        if self.original_exception:
            result["original_error"] = str(self.original_exception)
            result["original_type"] = type(self.original_exception).__name__
            
        return result

# Specific exception types
class ConfigurationError(ContributionError):
    """Error in application configuration"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)

class NetworkError(ContributionError):
    """Network-related error"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)

class APIError(ContributionError):
    """API-related error (GitHub, MCP, etc.)"""
    
    def __init__(self, 
                message: str, 
                status_code: Optional[int] = None, 
                endpoint: Optional[str] = None,
                **kwargs):
        """
        Initialize API error
        
        Args:
            message: Error message
            status_code: HTTP status code if applicable
            endpoint: API endpoint that caused the error
        """
        details = kwargs.get("details", {})
        if status_code is not None:
            details["status_code"] = status_code
        if endpoint is not None:
            details["endpoint"] = endpoint
            
        kwargs["details"] = details
        super().__init__(message, category=ErrorCategory.API, **kwargs)

class AuthenticationError(ContributionError):
    """Authentication-related error"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.AUTHENTICATION, **kwargs)

class GitError(ContributionError):
    """Git operation error"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.GIT, **kwargs)

class TimeoutError(ContributionError):
    """Timeout error"""
    
    def __init__(self, message: str, timeout_value: Optional[int] = None, **kwargs):
        details = kwargs.get("details", {})
        if timeout_value is not None:
            details["timeout_value"] = timeout_value
            
        kwargs["details"] = details
        super().__init__(message, category=ErrorCategory.TIMEOUT, **kwargs)

# Exception mapping
EXCEPTION_MAP = {
    # Python standard exceptions
    ValueError: ErrorCategory.INPUT_VALIDATION,
    TypeError: ErrorCategory.INPUT_VALIDATION,
    KeyError: ErrorCategory.CONFIGURATION,
    FileNotFoundError: ErrorCategory.CONFIGURATION,
    PermissionError: ErrorCategory.PERMISSION,
    ConnectionError: ErrorCategory.NETWORK,
    TimeoutError: ErrorCategory.TIMEOUT,
    # Third-party exceptions
    "requests.exceptions.ConnectionError": ErrorCategory.NETWORK,
    "requests.exceptions.Timeout": ErrorCategory.TIMEOUT,
    "requests.exceptions.RequestException": ErrorCategory.API,
    "github.GithubException": ErrorCategory.API,
    "git.exc.GitCommandError": ErrorCategory.GIT,
}

def get_error_category(exc: Exception) -> str:
    """
    Determine error category from exception
    
    Args:
        exc: Exception to categorize
        
    Returns:
        Error category string
    """
    # Check if exception is already categorized
    if isinstance(exc, ContributionError):
        return exc.category
    
    # Check exception type
    exc_type = type(exc)
    
    # Check direct match
    if exc_type in EXCEPTION_MAP:
        return EXCEPTION_MAP[exc_type]
    
    # Check string representation (for imported exceptions)
    exc_name = f"{exc_type.__module__}.{exc_type.__name__}"
    if exc_name in EXCEPTION_MAP:
        return EXCEPTION_MAP[exc_name]
    
    # Default to unknown
    return ErrorCategory.UNKNOWN

def create_error_from_exception(exc: Exception, 
                             message: Optional[str] = None) -> ContributionError:
    """
    Create appropriate ContributionError from any exception
    
    Args:
        exc: Source exception
        message: Custom message to use (if None, use str(exc))
        
    Returns:
        ContributionError instance
    """
    if isinstance(exc, ContributionError):
        return exc
    
    # Determine category
    category = get_error_category(exc)
    
    # Use provided message or exception string
    error_message = message or str(exc)
    
    # Create appropriate exception type based on category
    if category == ErrorCategory.CONFIGURATION:
        return ConfigurationError(error_message, original_exception=exc)
    elif category == ErrorCategory.NETWORK:
        return NetworkError(error_message, original_exception=exc)
    elif category == ErrorCategory.API:
        # Try to extract status code for API errors
        status_code = getattr(exc, "status_code", None)
        if status_code is None and hasattr(exc, "args") and len(exc.args) > 0:
            if isinstance(exc.args[0], dict) and "status" in exc.args[0]:
                status_code = exc.args[0]["status"]
        
        return APIError(error_message, status_code=status_code, original_exception=exc)
    elif category == ErrorCategory.AUTHENTICATION:
        return AuthenticationError(error_message, original_exception=exc)
    elif category == ErrorCategory.GIT:
        return GitError(error_message, original_exception=exc)
    elif category == ErrorCategory.TIMEOUT:
        return TimeoutError(error_message, original_exception=exc)
    else:
        # Generic ContributionError for other categories
        return ContributionError(error_message, category=category, original_exception=exc)

def handle_error(exc: Exception, 
                log_level: int = logging.ERROR,
                reraise: bool = True,
                error_message: Optional[str] = None) -> ContributionError:
    """
    Handle exception with proper logging and transformation
    
    Args:
        exc: Exception to handle
        log_level: Logging level to use
        reraise: Whether to reraise the exception
        error_message: Custom error message
        
    Returns:
        Transformed ContributionError
        
    Raises:
        ContributionError: If reraise is True
    """
    # Create appropriate error
    error = create_error_from_exception(exc, message=error_message)
    
    # Log error with appropriate level
    logger.log(log_level, error.message, exc_info=exc)
    
    # Include stack trace for severe errors
    if log_level >= logging.ERROR:
        error_dict = error.to_dict()
        error_dict["traceback"] = traceback.format_exc()
        logger.debug(f"Error details: {error_dict}")
    
    # Reraise if requested
    if reraise:
        raise error
        
    return error

def safe_operation(
    error_message: Optional[str] = None,
    log_level: int = logging.ERROR,
    reraise: bool = True,
    fallback_result: Any = None,
) -> Callable:
    """
    Decorator for safe operation with error handling
    
    Args:
        error_message: Custom error message template
        log_level: Logging level for errors
        reraise: Whether to reraise exceptions
        fallback_result: Result to return on error if not reraising
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Format error message with function name if not provided
                msg = error_message
                if msg is None:
                    msg = f"Error in {func.__name__}: {str(e)}"
                
                # Handle the error
                try:
                    handle_error(e, log_level=log_level, reraise=reraise, error_message=msg)
                except ContributionError as ce:
                    if reraise:
                        raise
                
                # Return fallback if not reraising
                return fallback_result
                
        return wrapper
    return decorator 