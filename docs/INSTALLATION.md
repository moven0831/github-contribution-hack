# Installation Guide for GitHub Contribution Hack

This guide provides detailed instructions for installing and setting up the GitHub Contribution Hack tool.

## Prerequisites

Before installation, ensure you have the following:

- **Python 3.x**: The application requires Python 3.6 or newer
- **Git**: Installed and configured on your system
- **GitHub Account**: With repository access
- **GitHub Personal Access Token**: With `repo` scope

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/github-contribution-hack.git
cd github-contribution-hack
```

### 2. Create and Activate a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit the `.env` file and add your credentials:

```
# GitHub Authentication
GITHUB_TOKEN=your_github_token_here

# MCP Integration (Optional)
MCP_API_KEY=your_mcp_api_key_here
MCP_API_ENDPOINT=https://api.mcp.dev/v1
```

### 5. Configure Application Settings

Edit the `config.yml` file to customize your settings:

```yaml
# GitHub settings
repositories:
  - yourusername/repo1
  - yourusername/repo2

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
  complexity: "medium"
  language_weights:
    python: 0.4
    javascript: 0.3
    markdown: 0.2
    text: 0.1

# Error handling
error_handling:
  log_level: INFO
  log_file: logs/application.log
  reraise_errors: true
  max_retries: 3
```

### 6. Setup Security (Optional)

For enhanced security with encrypted credentials:

```bash
python setup_security.py
```

This utility will guide you through:
- Encrypting your GitHub token
- Setting up system keyring integration
- Configuring credential rotation

## Verifying Installation

To verify your installation is working correctly:

```bash
# Run the test suite
python run_tests.py

# Check for any error messages or failures
```

## Running the Application

### Basic Usage

```bash
python main.py
```

### Running with Monitoring Dashboard

```bash
python main.py --monitor
```

### Test Mode (No Actual Commits)

To test without making actual commits:

```bash
python main.py --dry-run
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your GitHub token has the correct permissions
   - Check that your token is correctly set in `.env` or through the security setup

2. **Dependency Issues**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check for conflicting package versions

3. **Configuration Errors**
   - Validate your `config.yml` has the correct format
   - Ensure all required fields are present

### Getting Help

If you encounter issues not covered here:

1. Check the log files in `logs/`
2. Run with debug logging: `python main.py --debug`
3. Open an issue on the GitHub repository 