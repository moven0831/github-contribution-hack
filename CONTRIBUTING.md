# Contributing to GitHub Contribution Hack

Thank you for your interest in contributing to the GitHub Contribution Hack project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to foster an inclusive and respectful community.

## Getting Started

1. **Fork the Repository**
   
   Start by forking the repository on GitHub.

2. **Clone Your Fork**
   
   ```bash
   git clone https://github.com/yourusername/github-contribution-hack.git
   cd github-contribution-hack
   ```

3. **Set Up Development Environment**
   
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

4. **Create a Branch**
   
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code
- Use meaningful variable and function names
- Include docstrings for all functions, classes, and modules
- Maintain 100% test coverage for new features

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Changes to build process or auxiliary tools

Examples:
```
feat(api): add endpoint for repository analysis
fix(error-handling): properly catch and log API exceptions
docs(readme): update installation instructions
```

### Pull Request Process

1. **Update Documentation**
   
   Update the necessary documentation, including docstrings, README.md, and other relevant docs.

2. **Add Tests**
   
   Add tests for any new functionality or bug fixes.

3. **Run Tests**
   
   Ensure all tests pass:
   ```bash
   python run_tests.py
   ```

4. **Check Code Style**
   
   Run the linter to ensure code meets style guidelines:
   ```bash
   flake8 .
   ```

5. **Submit Pull Request**
   
   Submit your pull request with a clear description of the changes and reference any related issues.

6. **Code Review**
   
   Address any feedback from code review.

## Testing

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test files
pytest tests/test_mcp_integration.py

# Run with coverage report
pytest --cov=. tests/
```

### Adding Tests

- Add tests in the `tests/` directory
- Name test files with the `test_` prefix
- Name test functions with the `test_` prefix
- Mock external services where appropriate
- Cover both success and error paths

Example:
```python
def test_generate_content_success():
    """Test successful content generation."""
    client = MCPClient(api_key="test_key")
    content = client.generate_content(content_type="python")
    assert content is not None
    assert len(content) > 0

def test_generate_content_failure():
    """Test content generation with API failure."""
    client = MCPClient(api_key="invalid_key")
    with pytest.raises(APIError) as e:
        client.generate_content()
    assert "Authentication failed" in str(e.value)
```

## Feature Requests and Bug Reports

- Use the GitHub Issues section to report bugs or request features
- Use the provided templates for bug reports and feature requests
- Be specific and include steps to reproduce for bugs
- For feature requests, clearly explain the problem the feature would solve

## Documentation

When adding or updating features, please update the following documentation:

1. **API Documentation**: Update the `docs/API_REFERENCE.md` file
2. **User Guide**: Update README.md and relevant documentation in `docs/`
3. **Docstrings**: Maintain detailed docstrings in the code

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Questions?

If you have any questions or need help, please:

1. Check the existing issues on GitHub
2. Create a new issue if your question is not addressed
3. Reach out to the maintainers

Thank you for contributing to GitHub Contribution Hack! 