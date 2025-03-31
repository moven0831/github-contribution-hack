# GitHub Contribution Hack Documentation

Welcome to the comprehensive documentation for the GitHub Contribution Hack tool. This documentation is organized by topic to help you quickly find the information you need.

## Getting Started

- [Installation Guide](INSTALLATION.md) - Step-by-step instructions for setting up the tool
- [Demo Guide](../DEMO.md) - Quick start demonstration of the tool's capabilities

## Basic Configuration

- [Sample Configurations](SAMPLE_CONFIGURATIONS.md) - Ready-to-use configuration examples for different contribution patterns
- [Use Cases](USE_CASES.md) - Comprehensive examples for various scenarios and use cases

## Advanced Features

- [MCP Integration](../MCP_INTEGRATION.md) - Guide for AI-powered content generation
- [API Reference](API_REFERENCE.md) - Complete API documentation for developers

## Troubleshooting and Support

- [Troubleshooting Guide](TROUBLESHOOTING.md) - Solutions for common issues
- [Error Handling Guide](ERROR_HANDLING.md) - Detailed error handling documentation

## Best Practices and Guidelines

- [Best Practices](BEST_PRACTICES.md) - Guidelines for responsible and effective usage
- [Contributing](../CONTRIBUTING.md) - Guide for those who want to contribute to the project

## Command Reference

### Basic Commands

```bash
# Run the contribution hack with default settings
python main.py

# Run with monitoring dashboard
python main.py --monitor

# Start the web interface
python main.py --web [--host HOST] [--port PORT]

# Run in interactive CLI mode
python main.py --interactive
```

### Visualization Commands

```bash
# Generate all visualizations
python main.py --visualize all

# Generate specific visualization
python main.py --visualize [heatmap|streak|timeline|repo]
```

### Testing Commands

```bash
# Run all tests
python run_tests.py

# Run specific test file
pytest tests/test_specific_file.py

# Run tests with coverage report
pytest --cov=. tests/
```

### Security Commands

```bash
# Set up secure credential storage
python setup_security.py

# Rotate credentials
python setup_security.py --rotate

# Audit credential security
python setup_security.py --audit
```

### Analytics Commands

```bash
# Generate analytics report
python analytics.py --report [daily|weekly|monthly]

# Export analytics data
python analytics.py --export [csv|json]
```

## Configuration Reference

The GitHub Contribution Hack is highly configurable. Here's a quick reference of the main configuration sections in `config.yml`:

### Repository Configuration

```yaml
repositories:
  - username/repo1
  - username/repo2

# Repository-specific settings
repository_specific:
  - name: username/repo1
    min_commits: 2
    max_commits: 5
```

### Commit Settings

```yaml
min_commits: 1
max_commits: 3
min_interval: 12  # hours
max_interval: 24  # hours

split_commits:
  enabled: true
  max_lines_per_commit: 5
  message_prefix: "Update"
```

### Content Generation

```yaml
intelligent_patterns:
  enabled: true
  content_types: [documentation, code, config]
  time_distribution: poisson

mcp_integration:
  enabled: true
  complexity: "medium"  # low, medium, high
  language_weights:
    python: 0.4
    javascript: 0.3
    markdown: 0.2
    text: 0.1
```

### Scheduling

```yaml
scheduler:
  working_hours:
    start: 9  # 9 AM
    end: 17   # 5 PM
  weekend_activity: reduced  # none, reduced, normal, high
```

### User Interface

```yaml
ui:
  web_interface:
    enabled: true
    host: "127.0.0.1"
    port: 5000
  
  cli_interface:
    enabled: true
    color_scheme: "default"
```

### Monitoring

```yaml
monitoring:
  enabled: true
  dashboard_refresh: 300  # seconds
  verification_checks: true
```

### Notifications

```yaml
notifications:
  enabled: true
  email:
    enabled: true
    smtp_server: "smtp.example.com"
    # Additional email settings
  webhook:
    enabled: true
    url: "https://example.com/webhook"
  desktop:
    enabled: true
```

## Further Resources

- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Git Documentation](https://git-scm.com/doc)
- [Python GitHub Library (PyGithub)](https://pygithub.readthedocs.io/)
``` 