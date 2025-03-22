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
  - `AuthenticationError`: Authentication failures
  - `GitError`: Git operation failures
  - `TimeoutError`: Operation timeouts

Each exception includes:
- Error message
- Error category
- Optional recovery hint
- Optional additional details
- Original exception (if wrapping another exception)

## Error Categories

Errors are categorized to aid in appropriate handling:

| Category          | Description                              | Examples                             |
|-------------------|------------------------------------------|--------------------------------------|
| `configuration`   | Configuration-related issues             | Missing config files, invalid settings |
| `network`         | Network connectivity issues              | Connection failures, DNS errors      |
| `api`             | API communication problems               | Bad responses, rate limiting         |
| `authentication`  | Authentication failures                  | Invalid tokens, expired credentials  |
| `permission`      | Permission-related issues                | File access denied, repo permissions |
| `input_validation`| Invalid inputs                           | Type errors, validation failures     |
| `timeout`         | Operation timeouts                       | Network timeouts, long-running ops   |
| `git`             | Git operation failures                   | Merge conflicts, clone failures      |
| `runtime`         | General runtime errors                   | Logic errors, unexpected conditions  |
| `unknown`         | Uncategorized errors                     | Other exceptions                     |

## Retry Mechanism

The application includes an exponential backoff retry mechanism for operations that might fail due to transient issues:

```python
from retry import retry_with_backoff

@retry_with_backoff(retries=3, exceptions=(requests.RequestException, ConnectionError))
def fetch_data(url):
    # Code that might fail transiently
```

This decorator will:
1. Retry the operation up to 3 times
2. Apply exponential backoff between retries
3. Add jitter to prevent request storms
4. Support specific exception types for retry conditions

## Health Monitoring

The health monitoring system continuously checks the health of critical services:

- MCP API status
- GitHub API availability and rate limits
- Other configurable health checks

It provides:
- Real-time status information
- Historical status data
- Alerting on service degradation
- Automatic recovery when possible

## Logging

Enhanced logging provides detailed information about application activity:

- Standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured logging with contextual information
- File-based logging with rotation
- Console logging for real-time feedback

## Error Recovery

The system implements various recovery strategies:

1. **Automatic retries** for transient failures
2. **Fallback content generation** when MCP is unavailable
3. **Cached responses** for frequently used data
4. **Graceful degradation** when services are impaired

## Usage Examples

### Handling Errors with Context

```python
from error_handler import handle_error

try:
    # Code that might fail
except Exception as e:
    handle_error(e, error_message="Custom error message")
```

### Safe Operation Decorator

```python
from error_handler import safe_operation

@safe_operation(error_message="Failed to fetch data", reraise=False, fallback_result=[])
def fetch_data():
    # Code that might fail
    return data
```

### Health Monitoring

```python
from health_monitor import monitor

# Start monitoring in background
monitor.start_monitoring()

# Get current system status
status = monitor.get_overall_system_status()

# Register custom health check
def check_database():
    # Custom health check logic
    return {"status": "ok", "message": "Database is healthy"}

monitor.register_health_check("database", check_database, "Database")
```

## Configuration

Error handling behavior can be configured in `config.yml`:

```yaml
error_handling:
  log_level: INFO                # Logging level (DEBUG, INFO, WARNING, ERROR)
  log_file: logs/application.log # Log file path
  reraise_errors: true           # Whether to reraise handled errors
  max_retries: 3                 # Maximum retry attempts
  monitoring_interval: 300       # Health check interval (seconds)
```

## Troubleshooting

When encountering errors:

1. Check the log files for detailed error information
2. Use the health monitoring system to verify service status
3. Look for specific error categories to identify the issue type
4. Check recovery hints provided with exceptions

## Extending the System

To add new error types:

1. Create a new exception class inheriting from `ContributionError`
2. Add appropriate category mapping in `EXCEPTION_MAP`
3. Implement any specialized handling in the relevant modules 