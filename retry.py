"""
Retry mechanism with exponential backoff

Provides functions and decorators to implement retry logic with
configurable backoff for API calls and other operations that may fail.
"""
import time
import random
import logging
import functools
from typing import Callable, Any, Optional, Type, List, Union, Tuple

logger = logging.getLogger(__name__)

def retry_with_backoff(
    retries: int = 3,
    backoff_factor: float = 1.5,
    max_backoff: float = 60.0,
    initial_wait: float = 1.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
) -> Callable:
    """
    Retry decorator with exponential backoff
    
    Args:
        retries: Maximum number of retries
        backoff_factor: Multiplier for backoff
        max_backoff: Maximum wait time between retries
        initial_wait: Initial wait time
        jitter: Add random jitter to wait time
        exceptions: Exception types to catch and retry
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            wait_time = initial_wait
            
            for attempt in range(1, retries + 2):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt > retries:
                        logger.error(f"Failed after {retries} retries: {str(e)}")
                        raise
                    
                    # Calculate next wait time with exponential backoff
                    if jitter:
                        sleep_time = min(max_backoff, wait_time * (1 + random.random() * 0.1))
                    else:
                        sleep_time = min(max_backoff, wait_time)
                    
                    logger.warning(
                        f"Attempt {attempt}/{retries + 1} failed: {str(e)}. "
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )
                    
                    time.sleep(sleep_time)
                    wait_time = wait_time * backoff_factor
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class RetryableHTTP:
    """Helper class for retryable HTTP operations"""
    
    @staticmethod
    def is_retryable_error(status_code: Optional[int]) -> bool:
        """
        Determine if a status code represents a retryable error
        
        Args:
            status_code: HTTP status code
            
        Returns:
            True if the error is retryable, False otherwise
        """
        if status_code is None:
            return True  # Network errors (no status code)
        
        # 429 Too Many Requests
        # 500, 502, 503, 504 Server errors
        return status_code in (429, 500, 502, 503, 504)
    
    @staticmethod
    def calculate_retry_after(
        response_headers: dict, 
        default_backoff: float, 
        max_backoff: float
    ) -> float:
        """
        Calculate retry time based on response headers
        
        Args:
            response_headers: HTTP response headers
            default_backoff: Default backoff time if no header is found
            max_backoff: Maximum backoff time
            
        Returns:
            Backoff time in seconds
        """
        # Check for Retry-After header (could be seconds or HTTP date)
        retry_after = response_headers.get('Retry-After')
        
        if retry_after:
            try:
                # Try to parse as integer seconds
                return min(float(retry_after), max_backoff)
            except ValueError:
                # Could be an HTTP date format, use default for simplicity
                pass
        
        # Use default backoff
        return default_backoff 