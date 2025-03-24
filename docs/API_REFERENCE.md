# API Reference

This document provides detailed information about the main modules, classes, and functions in the GitHub Contribution Hack tool.

## Core Modules

### `main.py`

The main entry point and orchestrator for the GitHub Contribution Hack application.

#### `GitHubContributionHack` Class

```python
GitHubContributionHack(config_path='config.yml')
```

**Parameters:**
- `config_path` (str): Path to the YAML configuration file.

**Methods:**

| Method | Description |
|--------|-------------|
| `make_contributions()` | Main method to generate and push contributions according to configuration settings. |
| `generate_random_content()` | Generates random content for commits. |
| `start_monitoring()` | Starts the monitoring dashboard. |

**Usage Example:**

```python
from main import GitHubContributionHack

# Initialize with default config
hack = GitHubContributionHack()

# Initialize with custom config
hack = GitHubContributionHack(config_path='custom_config.yml')

# Generate and push contributions
hack.make_contributions()

# Start monitoring dashboard
hack.start_monitoring()
```

### `mcp_integration.py`

Provides integration with the MCP (Mission Control Protocol) for enhanced AI-powered content generation.

#### `MCPClient` Class

```python
MCPClient(api_key=None, endpoint=None)
```

**Parameters:**
- `api_key` (str, optional): MCP API key. If None, loads from environment variables.
- `endpoint` (str, optional): MCP API endpoint. If None, uses default endpoint.

**Methods:**

| Method | Description |
|--------|-------------|
| `generate_content(content_type=None, complexity=None, context=None)` | Generates content using MCP AI. |
| `analyze_repository(repo_url, branch='main')` | Analyzes repository structure and patterns. |

**Usage Example:**

```python
from mcp_integration import MCPClient, get_mcp_client

# Using environment variables for credentials
client = get_mcp_client()

# Generate Python code
python_code = client.generate_content(
    content_type='python',
    complexity='medium',
    context={'purpose': 'data processing'}
)

# Generate commit message
commit_message = client.generate_content(
    content_type='commit_message',
    context={'changes': ['Added new feature', 'Fixed bug in login']}
)
```

### `analytics.py`

Provides analytics and statistics about contribution patterns and activity.

#### `ContributionAnalytics` Class

```python
ContributionAnalytics(db_path='contributions.db')
```

**Parameters:**
- `db_path` (str): Path to the SQLite database for storing contribution data.

**Methods:**

| Method | Description |
|--------|-------------|
| `record_contribution(repo, files, timestamp=None)` | Records a contribution to the database. |
| `get_streak_data()` | Returns data about the current contribution streak. |
| `generate_report(report_type='summary', start_date=None, end_date=None)` | Generates analytics report. |
| `export_data(format='csv', path=None)` | Exports contribution data. |

**Usage Example:**

```python
from analytics import ContributionAnalytics

# Initialize analytics
analytics = ContributionAnalytics()

# Record a contribution
analytics.record_contribution(
    repo="user/repo",
    files=["README.md", "src/feature.py"],
    timestamp="2023-10-15T14:32:00Z"
)

# Get streak information
streak_data = analytics.get_streak_data()
print(f"Current streak: {streak_data['current_streak']} days")

# Generate weekly report
report = analytics.generate_report(
    report_type='weekly',
    end_date='2023-10-15'
)
```

### `error_handler.py`

Provides centralized error handling and custom exceptions.

#### Exception Hierarchy

- `ContributionError`: Base exception for all application errors
  - `ConfigurationError`: Configuration-related errors
  - `NetworkError`: Network connectivity issues
  - `APIError`: API-related errors
  - `AuthenticationError`: Authentication failures
  - `GitError`: Git operation failures
  - `TimeoutError`: Operation timeouts

#### Functions

| Function | Description |
|--------|-------------|
| `handle_error(exc, log_level=logging.ERROR, reraise=True, error_message=None)` | Central error handler. |
| `safe_operation(error_message=None, log_level=logging.ERROR, reraise=True, fallback_result=None)` | Decorator for error-prone operations. |
| `get_error_category(exc)` | Determines the error category for an exception. |

**Usage Example:**

```python
from error_handler import handle_error, safe_operation, APIError
import logging

# Handling exceptions manually
try:
    # Some code that might fail
    pass
except Exception as e:
    error = handle_error(
        e,
        log_level=logging.WARNING,
        reraise=False,
        error_message="Custom error message"
    )
    
# Using the safe_operation decorator
@safe_operation(
    error_message="Failed to process data",
    reraise=False,
    fallback_result=[]
)
def process_data():
    # Code that might fail
    return processed_data

# Creating custom API error
def call_api():
    response = requests.get('https://api.example.com')
    if response.status_code != 200:
        raise APIError(
            message="API request failed",
            status_code=response.status_code,
            endpoint="api.example.com"
        )
```

### `health_monitor.py`

Provides health monitoring for critical services.

#### `HealthMonitor` Class

```python
HealthMonitor()
```

**Methods:**

| Method | Description |
|--------|-------------|
| `start_monitoring()` | Starts the health monitoring background threads. |
| `stop_monitoring()` | Stops the health monitoring. |
| `get_health_status()` | Gets the current health status of all monitored services. |
| `register_health_check(id, check_func, display_name, interval_seconds=300)` | Registers a custom health check. |

**Usage Example:**

```python
from health_monitor import monitor

# Start monitoring with default checks
monitor.start_monitoring()

# Register a custom health check
def check_database():
    # Database health check logic
    return {
        "status": "ok",
        "message": "Database is connected",
        "details": {"tables": 10, "size_mb": 25}
    }

monitor.register_health_check(
    "database",
    check_database,
    "Database Health",
    interval_seconds=60
)

# Get current health status
status = monitor.get_health_status()
print(f"All systems healthy: {all(s['healthy'] for s in status.values())}")
```

### `retry.py`

Provides retry mechanisms for operations that might fail transiently.

#### Functions

| Function | Description |
|--------|-------------|
| `retry_with_backoff(retries=3, exceptions=Exception, base_delay=1.0, max_delay=60.0, factor=2.0, jitter=True, should_retry_func=None, on_retry=None)` | Decorator for retrying operations with exponential backoff. |

**Parameters:**
- `retries` (int): Maximum number of retry attempts.
- `exceptions` (Exception or tuple): Exception types to catch and retry.
- `base_delay` (float): Initial delay between retries in seconds.
- `max_delay` (float): Maximum delay between retries in seconds.
- `factor` (float): Multiplier for exponential backoff.
- `jitter` (bool): Add randomness to delay to prevent request storms.
- `should_retry_func` (callable): Function to determine if retry should occur.
- `on_retry` (callable): Function to call on each retry attempt.

**Usage Example:**

```python
from retry import retry_with_backoff
import requests

@retry_with_backoff(
    retries=5,
    exceptions=(requests.RequestException, ConnectionError),
    base_delay=2.0,
    max_delay=30.0
)
def fetch_data_from_api(url):
    """Fetch data with automatic retries"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

### `logger_config.py`

Provides logging configuration for the application.

#### Functions

| Function | Description |
|--------|-------------|
| `setup_logging(log_file='app.log', log_level='INFO', max_size_mb=10, backup_count=5, include_console=True)` | Configures application-wide logging. |
| `with_context(**context_data)` | Context manager for adding contextual information to logs. |

**Usage Example:**

```python
from logger_config import setup_logging, with_context
import logging

# Configure logging
setup_logging(
    log_file='logs/app.log',
    log_level='DEBUG',
    max_size_mb=5,
    backup_count=3
)

logger = logging.getLogger(__name__)

# Add context to log messages
with with_context(module='authentication', user_id='12345'):
    logger.info("User logged in")
    logger.debug("Session created", extra={"session_id": "abc123"})
```

## Configuration Reference

### `config.yml`

The main configuration file for the GitHub Contribution Hack.

```yaml
# GitHub settings
github_token: your_github_token_here  # Only if not using encrypted storage
repositories:
  - username/repo1
  - username/repo2
 
# Commit settings
min_commits: 1
max_commits: 3
min_interval: 12  # hours
max_interval: 24  # hours

# Content generation
split_commits:
  enabled: true
  max_lines_per_commit: 10
  message_prefix: "Update"

# MCP Integration
mcp_integration:
  enabled: true
  complexity: "medium"  # low, medium, high
  language_weights:
    python: 0.4
    javascript: 0.3
    markdown: 0.2
    text: 0.1
  repository_analysis: true
  content_quality: "high"
  dry_run: false

# Error handling
error_handling:
  log_level: INFO
  log_file: logs/application.log
  max_log_size_mb: 10
  log_backup_count: 5
  reraise_errors: true
  max_retries: 3
  monitoring_interval: 300
  alerts_enabled: true
```

## Environment Variables

The following environment variables can be defined in the `.env` file:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token with repo scope |
| `MCP_API_KEY` | API key for MCP integration |
| `MCP_API_ENDPOINT` | Custom endpoint for MCP API |
| `LOG_LEVEL` | Logging level (overrides config.yml) |
| `ENCRYPTION_KEY` | Key for token encryption (auto-generated if not provided) |
| `MONITORING_ENABLED` | Enable/disable monitoring (1/0) |

## Database Schema

### `contributions.db`

SQLite database containing contribution data.

#### Tables

**contributions**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| repository | TEXT | Repository name |
| timestamp | DATETIME | Contribution timestamp |
| files_changed | INTEGER | Number of files changed |
| additions | INTEGER | Lines added |
| deletions | INTEGER | Lines deleted |
| commit_hash | TEXT | Git commit hash |
| verified | BOOLEAN | Whether contribution was verified |

**repositories**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Repository name |
| last_contribution | DATETIME | Last contribution timestamp |
| total_contributions | INTEGER | Total number of contributions |
| active | BOOLEAN | Whether repository is active | 