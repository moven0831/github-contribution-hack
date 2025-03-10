# GitHub Contribution Hack Tests

This directory contains unit tests for the GitHub Contribution Hack, focusing on MCP integration.

## Test Structure

- `test_mcp_integration.py`: Tests for the MCP client and API integration
- `test_main_mcp.py`: Tests for MCP integration in the main GitHub Contribution Hack script

## Running Tests

You can run the tests using the provided `run_tests.py` script from the root directory:

```bash
python run_tests.py
```

This will run all tests and generate a coverage report.

Alternatively, you can use pytest directly:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_integration --cov=main tests/

# Run specific test file
pytest tests/test_mcp_integration.py
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

## Adding New Tests

When adding new tests:

1. Maintain the same naming convention (`test_*.py`)
2. Follow the same structure with proper setup/teardown methods
3. Use mocking to avoid external dependencies
4. Update the requirements.txt if new test dependencies are needed 