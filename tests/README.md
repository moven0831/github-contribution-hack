# GitHub Contribution Hack Tests

This directory contains tests for the GitHub Contribution Hack, focusing on MCP integration and core functionality.

## Test Structure

- `test_mcp_integration.py`: Tests for the MCP client and API integration
- `test_main_mcp.py`: Tests for MCP integration in the main GitHub Contribution Hack script
- `conftest.py`: Shared pytest fixtures and test configuration

## Running Tests

You can run the tests using the improved `run_tests.py` script from the root directory:

```bash
# Run all tests with default settings
python run_tests.py

# Run with specific options
python run_tests.py --no-html --no-report  # No HTML report, no console output
python run_tests.py --no-parallel          # Disable parallel test execution
python run_tests.py --test-dir custom_tests # Run tests from a different directory
python run_tests.py --pattern "test_mcp*.py" # Only run tests matching the pattern
python run_tests.py --source main.py mcp_integration.py # Only track coverage for these files
```

The script now supports parallel test execution for faster results.

Alternatively, you can use pytest directly:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_mcp_integration.py

# Run tests with specific markers
pytest -m "not slow"

# Run tests with verbose output
pytest -v
```

## Fixtures and Test Helpers

The `conftest.py` file provides several useful fixtures to make writing tests easier:

- `temp_config_file`: Creates a temporary configuration file for testing
- `mock_environment`: Sets up test environment variables
- `mock_mcp_client`: Provides a pre-configured mock MCP client
- `github_hack_patches`: Applies common patches for GitHubContributionHack tests

Example using these fixtures:

```python
def test_something(temp_config_file, mock_environment, mock_mcp_client):
    # Your test code using the fixtures
    pass
```

## Test Coverage

The tests aim to cover:

1. **MCP Client Functionality**:
   - API communication
   - Code generation
   - Commit message generation
   - Repository analysis
   - Fallback mechanisms

2. **Integration with Main Script**:
   - Initialization with MCP
   - Content generation flow
   - Fallback to standard generation
   - File type detection

3. **Error Handling and Retry Logic**:
   - Exception handling
   - Retry mechanisms
   - Graceful degradation

## Adding New Tests

When adding new tests:

1. Use pytest style tests (function-based) for new tests
2. Leverage the fixtures in `conftest.py` to simplify setup/teardown
3. Add appropriate marks for categorization (`@pytest.mark.slow`, etc.)
4. Follow these naming conventions:
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*`
5. Write docstrings for test functions/classes to explain what's being tested

Example of a good test:

```python
import pytest

@pytest.mark.integration
def test_mcp_code_generation(mock_mcp_client, temp_config_file):
    """Test that MCP client correctly generates code with expected parameters"""
    # Test implementation here
    pass
```

## Continuous Integration

These tests are designed to be run in CI environments. The exit code from `run_tests.py` indicates test success/failure for CI pipelines 