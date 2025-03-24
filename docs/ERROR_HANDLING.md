# Error Handling and Resilience

This document outlines the enhanced error handling and resilience features of the GitHub Contribution Hack tool.

## Overview

The error handling system provides:

1. **Standardized error handling** across the application
2. **Categorized exceptions** for different types of errors
3. **Automatic retry mechanisms** for transient failures
4. **Health monitoring** for critical services
5. **Detailed logging** for debugging and troubleshooting
6. **Fallback mechanisms** when services are unavailable

## Custom Exceptions

The application uses a hierarchy of custom exceptions to provide detailed information about errors:

- `ContributionError`: Base class for all application-specific exceptions
  - `ConfigurationError`: Configuration-related errors
  - `NetworkError`: Network connectivity issues
  - `APIError`: API-related errors (GitHub, MCP)
    - Contains `status_code` and `endpoint` information for API errors
  - `AuthenticationError`: Authentication failures
  - `GitError`: Git operation failures
  - `TimeoutError`: Operation timeouts

Each exception includes:
- Error message
- Error category
- Optional recovery hint
- Optional additional details
- Original exception (if wrapping another exception)

### Example: Creating and Handling Custom Exceptions

```python
from error_handler import APIError, handle_error

try:
    # Attempt API call
    response = requests.get('https://api.github.com/repos/user/repo')
    
    if response.status_code != 200:
        raise APIError(
            message="Failed to fetch repository data",
            status_code=response.status_code,
            endpoint="api.github.com/repos/user/repo",
            recovery_hint="Check repository name and permissions"
        )
        
    # Process response data
    data = response.json()
    
except Exception as e:
    # Handle any exception, automatically categorizing it
    error = handle_error(
        e, 
        error_message="Repository access error occurred", 
        reraise=False
    )
    
    # Access error details
    print(f"Error category: {error.category}")
    print(f"Recovery hint: {error.recovery_hint}")
```

## Error Categories

Errors are categorized to aid in appropriate handling:

| Category          | Description                              | Examples                             | Typical Handling |
|-------------------|------------------------------------------|--------------------------------------|------------------|
| `configuration`   | Configuration-related issues             | Missing config files, invalid settings | Fix configuration file or settings |
| `network`         | Network connectivity issues              | Connection failures, DNS errors      | Retry after delay, check connectivity |
| `api`             | API communication problems               | Bad responses, rate limiting         | Respect rate limits, retry with backoff |
| `authentication`  | Authentication failures                  | Invalid tokens, expired credentials  | Prompt for new credentials |
| `permission`      | Permission-related issues                | File access denied, repo permissions | Request proper permissions |
| `input_validation`| Invalid inputs                           | Type errors, validation failures     | Fix input values |
| `timeout`         | Operation timeouts                       | Network timeouts, long-running ops   | Retry with longer timeout |
| `git`             | Git operation failures                   | Merge conflicts, clone failures      | Repair git state |
| `runtime`         | General runtime errors                   | Logic errors, unexpected conditions  | Fix application logic |
| `unknown`         | Uncategorized errors                     | Other exceptions                     | Debug and categorize |

## Retry Mechanism

The application includes an exponential backoff retry mechanism for operations that might fail due to transient issues.

### Basic Retry Example

```python
from retry import retry_with_backoff
import requests

@retry_with_backoff(
    retries=3,
    exceptions=(requests.RequestException, ConnectionError),
    base_delay=1.0,  # 1 second initial delay
    max_delay=30.0,  # maximum 30 seconds between retries
    jitter=True      # add randomness to prevent request storms
)
def fetch_github_data(repo_name):
    """Fetch data from GitHub with automatic retries"""
    url = f"https://api.github.com/repos/{repo_name}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

### Customizing Retry Behavior

```python
from retry import retry_with_backoff, RetryExhaustedError

# Custom condition to retry only on specific HTTP status codes
def should_retry(exception):
    if isinstance(exception, requests.RequestException):
        if hasattr(exception, 'response') and exception.response is not None:
            # Retry on rate limiting (429) or server errors (5xx)
            return exception.response.status_code in [429] or \
                   500 <= exception.response.status_code < 600
    return False

@retry_with_backoff(
    retries=5,
    exceptions=requests.RequestException,
    should_retry_func=should_retry,
    on_retry=lambda attempt, delay: print(f"Retry attempt {attempt} after {delay:.2f}s")
)
def create_github_commit(repo_name, file_path, content, message):
    # API call that might be rate-limited or temporarily fail
    # ...

try:
    create_github_commit('user/repo', 'README.md', 'New content', 'Update README')
except RetryExhaustedError as e:
    print(f"Failed after {e.attempts} attempts: {e}")
```

## Health Monitoring

The health monitoring system continuously checks the health of critical services with configurable thresholds.

### Setting Up Service Monitoring

```python
from health_monitor import monitor

# Configure thresholds for health indicators
monitor.configure(
    thresholds={
        'github_api': {
            'max_response_time': 2.0,  # seconds
            'min_rate_limit_remaining': 50  # GitHub API rate limit remaining
        },
        'mcp_api': {
            'max_response_time': 1.5  # seconds
        }
    }
)

# Start monitoring in background
monitor.start_monitoring()

# Get current health status
status = monitor.get_health_status()
if not status['github_api']['healthy']:
    print(f"GitHub API issue: {status['github_api']['message']}")
```

### Custom Health Checks

```python
from health_monitor import monitor
import sqlite3

def check_database_connection():
    """Check that database is available and not corrupted"""
    try:
        conn = sqlite3.connect('contributions.db')
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM sqlite_master")
        result = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "ok" if result > 0 else "warning",
            "message": "Database connected and has tables" if result > 0 else "Database is empty",
            "details": {"tables_count": result}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
            "details": {"error": str(e)}
        }

# Register custom health check to run every 5 minutes
monitor.register_health_check(
    "database", 
    check_database_connection,
    "Database Connection",
    interval_seconds=300
)
```

## Logging

Enhanced logging provides detailed information about application activity through structured logging.

### Configuring Logging

```python
from logger_config import setup_logging

# Setup application-wide logging with file rotation
setup_logging(
    log_file="logs/application.log",
    log_level="INFO",
    max_size_mb=10,
    backup_count=5,
    include_console=True
)

# Using the configured logger
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed debug information")
logger.info("Normal operation information")
logger.warning("Warning: something might be wrong")
logger.error("Error: operation failed", exc_info=True)  # Include stack trace
```

### Contextual Logging

```python
from logger_config import with_context

# Add contextual information to logs
with with_context(repository="user/repo", operation="commit"):
    logger.info("Creating new commit")
    # All logs within this context will include repository and operation fields
    
# For specific log messages
logger.info("Pushed changes", extra={"commit_hash": "abc123", "files_changed": 5})
```

## Error Recovery

The system implements various recovery strategies:

### Safe Operation Decorator

The `safe_operation` decorator makes functions more resilient by automatically handling exceptions.

```python
from error_handler import safe_operation
import logging

@safe_operation(
    error_message="Failed to process repository data",
    log_level=logging.WARNING,  # Less critical, so use WARNING level
    reraise=False,  # Don't reraise, return fallback instead
    fallback_result={"status": "unavailable", "commits": []}
)
def process_repository_data(repo_name):
    # Code that might fail
    # If an exception occurs, log it and return the fallback_result
    return {"status": "success", "commits": get_commits(repo_name)}

# Usage - will never raise an exception due to reraise=False
result = process_repository_data("user/repo") 
```

### Graceful Degradation

```python
from error_handler import handle_error
from mcp_integration import MCPClient

def generate_content():
    """Generate content with fallback to simpler method if MCP fails"""
    try:
        # Try the more sophisticated MCP content generation
        mcp_client = MCPClient()
        return mcp_client.generate_content()
    except Exception as e:
        # Handle error but don't reraise
        handle_error(e, error_message="MCP generation failed, using fallback", reraise=False)
        
        # Fall back to simpler generation method
        return generate_basic_content()
```

## Configuration

Error handling behavior can be configured in `config.yml`:

```yaml
error_handling:
  # Logging configuration
  log_level: INFO                # Logging level (DEBUG, INFO, WARNING, ERROR)
  log_file: logs/application.log # Log file path
  max_log_size_mb: 10            # Maximum log file size before rotation
  log_backup_count: 5            # Number of backup log files to keep
  
  # Error handling behavior
  reraise_errors: true           # Whether to reraise handled errors
  max_retries: 3                 # Maximum retry attempts for retryable operations
  base_retry_delay: 1.0          # Base delay between retries (seconds)
  max_retry_delay: 60.0          # Maximum delay between retries (seconds)
  
  # Monitoring configuration
  monitoring_enabled: true       # Enable health monitoring
  monitoring_interval: 300       # Health check interval (seconds)
  alerts_enabled: true           # Enable alerts for health issues
```

## Best Practices

1. **Use appropriate error categories** to ensure consistent handling
2. **Add recovery hints** to help users resolve issues
3. **Include contextual details** in error objects
4. **Implement retries** for network and API operations
5. **Use safe operation decorators** for non-critical functions
6. **Implement fallback mechanisms** for critical features
7. **Monitor service health** proactively

## Extending the Error Handling System

### Adding a New Exception Type

```python
from error_handler import ContributionError, ErrorCategory

class DatabaseError(ContributionError):
    """Exception raised for database-related errors"""
    
    def __init__(self, 
                message: str, 
                query: str = None, 
                **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,  # Add this to ErrorCategory class
            details={"query": query, **kwargs.get("details", {})},
            **kwargs
        )
        self.query = query
```

### Registering Exception Mapping

Update the `get_error_category` function to handle your new exception type:

```python
def get_error_category(exc: Exception) -> str:
    # Add to the existing mapping
    EXCEPTION_MAP = {
        # ... existing mappings
        sqlite3.Error: ErrorCategory.DATABASE,
        sqlite3.OperationalError: ErrorCategory.DATABASE,
        # ... add other database error types
    }
    
    # Rest of the function remains the same
``` 