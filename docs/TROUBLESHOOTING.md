# Troubleshooting Guide

This document provides solutions to common issues you might encounter when using the GitHub Contribution Hack.

## Authentication Issues

### GitHub API Rate Limiting

**Symptoms:** 
- Error messages containing "API rate limit exceeded"
- Commits failing to push
- Error code 403 from GitHub API

**Solutions:**
1. **Check token permissions**: Ensure your GitHub token has the correct `repo` scope
   ```bash
   python main.py --check-auth
   ```

2. **Implement exponential backoff**: Modify config.yml to include retry settings
   ```yaml
   error_handling:
     github_rate_limit_retry: true
     max_retries: 5
     exponential_backoff: true
   ```

3. **Schedule during off-peak hours**: Configure the tool to run during times with lower API usage
   ```yaml
   scheduler:
     working_hours:
       start: 23  # 11 PM
       end: 5     # 5 AM
   ```

### Token Expiration or Revocation

**Symptoms:**
- Consistent authentication failures
- "Bad credentials" errors
- No commits appearing on GitHub

**Solutions:**
1. **Generate a new token**: Create a new personal access token on GitHub
   ```bash
   # Run the security setup utility with the new token
   python setup_security.py --renew
   ```

2. **Check token storage**: Verify your token is correctly stored
   ```bash
   python main.py --check-token
   ```

3. **Update environment variables**: If not using secure storage, update your .env file
   ```
   GITHUB_TOKEN=your_new_token_here
   ```

## Repository Issues

### Repository Not Found

**Symptoms:**
- "Repository not found" errors
- "Not Found" (404) GitHub API responses

**Solutions:**
1. **Verify repository names**: Check that repositories listed in config.yml exist and are accessible
   ```bash
   python main.py --verify-repos
   ```

2. **Check access permissions**: Ensure your token has access to the specified repositories
   ```bash
   python main.py --test-push --repo yourusername/repo-name
   ```

3. **Remove problematic repositories**: Edit config.yml to remove repositories causing issues

### Merge Conflicts

**Symptoms:**
- Push failures due to conflicts
- Error messages containing "failed to push some refs"

**Solutions:**
1. **Enable force push** (use with caution):
   ```yaml
   repositories:
     - name: yourusername/repo-name
       force_push: true  # Use with caution
   ```

2. **Enable pull before push**:
   ```yaml
   repositories:
     - name: yourusername/repo-name
       pull_before_push: true
   ```

3. **Clear local repository cache**:
   ```bash
   python main.py --clear-cache
   ```

## Content Generation Issues

### MCP Integration Failures

**Symptoms:**
- Errors related to MCP API
- Fallback to basic content generation
- No varied content despite MCP being enabled

**Solutions:**
1. **Verify MCP API key**:
   ```bash
   python main.py --test-mcp
   ```

2. **Check MCP service status**:
   ```bash
   python main.py --check-mcp-status
   ```

3. **Enable fallback mechanisms**:
   ```yaml
   mcp_integration:
     enabled: true
     fallback_on_failure: true
     fallback_retry_hours: 6  # Try MCP again after 6 hours
   ```

### Empty or Invalid Commits

**Symptoms:**
- Commits with no actual changes
- Error messages about empty commits
- Git rejecting pushes

**Solutions:**
1. **Ensure content generation**:
   ```yaml
   intelligent_patterns:
     min_content_size: 10  # Minimum characters
     ensure_modified_files: true
   ```

2. **Run in debug mode** to inspect content:
   ```bash
   python main.py --debug
   ```

3. **Check file modification logic**:
   ```bash
   python main.py --test-content-gen
   ```

## Performance Issues

### High CPU/Memory Usage

**Symptoms:**
- System slowing down when the tool is running
- Memory errors
- High CPU utilization

**Solutions:**
1. **Limit concurrent operations**:
   ```yaml
   performance:
     max_workers: 2
     parallel_repos: false
   ```

2. **Reduce repository cloning**:
   ```yaml
   performance:
     shallow_clone: true
     clone_depth: 1
   ```

3. **Optimize content generation**:
   ```yaml
   mcp_integration:
     complexity: "low"  # Reduce complexity
   ```

### Slow Execution

**Symptoms:**
- Operations taking much longer than expected
- Timeouts 
- Incomplete runs

**Solutions:**
1. **Enable caching**:
   ```yaml
   performance:
     repo_caching: true
     api_response_cache: true
     cache_ttl: 3600  # seconds
   ```

2. **Reduce repositories or commit frequency**:
   ```yaml
   min_commits: 1
   max_commits: 2
   repositories:  # Limit number of repositories
     - yourusername/primary-repo
   ```

3. **Profile and optimize**:
   ```bash
   python main.py --profile
   ```

## Monitoring and Analytics Issues

### Dashboard Not Showing Data

**Symptoms:**
- Empty monitoring dashboard
- Missing visualizations
- "No data available" messages

**Solutions:**
1. **Check data storage**:
   ```bash
   python main.py --check-db
   ```

2. **Rebuild analytics database**:
   ```bash
   python main.py --rebuild-analytics
   ```

3. **Enable verbose logging**:
   ```yaml
   monitoring:
     debug_mode: true
     log_level: DEBUG
   ```

### Incorrect Contribution Statistics

**Symptoms:**
- Dashboard statistics don't match GitHub
- Incorrect streak calculations
- Verification failures

**Solutions:**
1. **Force GitHub verification**:
   ```bash
   python main.py --verify-contributions
   ```

2. **Reset local statistics**:
   ```bash
   python main.py --reset-stats
   ```

3. **Synchronize with GitHub**:
   ```bash
   python main.py --sync-github
   ```

## Web Interface Issues

### Web Interface Not Starting

**Symptoms:**
- Cannot access the web interface
- Port already in use errors
- Connection refused errors

**Solutions:**
1. **Change port**:
   ```bash
   python main.py --web --port 8081
   ```

2. **Check for running instances**:
   ```bash
   # On Linux/macOS
   ps aux | grep main.py
   
   # On Windows
   tasklist | findstr python
   ```

3. **Force restart**:
   ```bash
   python main.py --restart-web
   ```

### Visualization Errors

**Symptoms:**
- Broken charts or graphs
- JavaScript errors in browser console
- "Unable to load visualization" messages

**Solutions:**
1. **Clear browser cache**: 
   - Press Ctrl+F5 in your browser

2. **Rebuild visualization data**:
   ```bash
   python main.py --rebuild-viz
   ```

3. **Check browser compatibility**:
   ```bash
   python main.py --web --compat-mode
   ```

## Installation and Environment Issues

### Dependency Conflicts

**Symptoms:**
- Import errors
- Package not found errors
- Version conflicts

**Solutions:**
1. **Use a fresh virtual environment**:
   ```bash
   python -m venv fresh_venv
   source fresh_venv/bin/activate  # On Linux/macOS
   fresh_venv\Scripts\activate      # On Windows
   pip install -r requirements.txt
   ```

2. **Check for conflicting packages**:
   ```bash
   pip check
   ```

3. **Install a specific version**:
   ```bash
   # For example, if PyGithub is causing issues
   pip uninstall PyGithub
   pip install PyGithub==2.1.1
   ```

### Security Setup Failures

**Symptoms:**
- Keyring access errors
- Encryption/decryption failures
- Permission denied errors

**Solutions:**
1. **Reinstall security components**:
   ```bash
   pip uninstall -y keyring cryptography
   pip install keyring cryptography
   ```

2. **Bypass keyring** (less secure fallback):
   ```yaml
   security:
     use_keyring: false
     use_env_directly: true  # Less secure
   ```

3. **Fix permissions**:
   ```bash
   # On Linux/macOS
   chmod 600 .env
   ```

## Getting Additional Help

If you're still experiencing issues:

1. **Enable diagnostic mode**:
   ```bash
   python main.py --diagnostic > diagnostic_log.txt
   ```

2. **Create an issue** on the project's GitHub repository with:
   - Description of the problem
   - Steps to reproduce
   - Content of diagnostic_log.txt (remove any sensitive information)

3. **Check logs** for detailed error information:
   ```bash
   # Default log location
   cat logs/application.log
   ```
``` 