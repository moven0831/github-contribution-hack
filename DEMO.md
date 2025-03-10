# GitHub Contribution Hack Demo

This demo showcases how the GitHub Contribution Hack automatically generates contributions to maintain a consistent streak.

## Demo Setup

1. Install the required Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Update the `config.yml` file with your settings:
   - Add your GitHub access token (generate one with `repo` scope) 
   - Specify the repositories you want to contribute to in the `repositories` list
   - Adjust `min_commits` and `max_commits` to set the number of commits made per run
   - Set `min_interval` and `max_interval` (in hours) to control the time between runs
   - Optionally enable the `split_commits` feature to split large commits into smaller ones:
     - Set `enabled` to `true` 
     - Specify the `max_lines_per_commit` to control the size of each split commit
     - Provide a `message_prefix` that will be included in each split commit message
   - Enable MCP integration for enhanced AI-powered content generation:
     - Set `mcp_integration.enabled` to `true`
     - Configure language preferences and complexity settings

   Example `config.yml`:
   ```yaml
   github_token: your_github_token_here
   repositories:
     - yourusername/repo1 
     - yourusername/repo2
   min_commits: 3
   max_commits: 5
   min_interval: 20 
   max_interval: 24
   split_commits:
     enabled: true
     max_lines_per_commit: 10
     message_prefix: "Split commit"
   mcp_integration:
     enabled: true
     complexity: "medium"
     language_weights:
       python: 0.4
       javascript: 0.3
       markdown: 0.2
       text: 0.1
   ```

3. Set up MCP API credentials (optional but recommended):
   - Obtain an MCP API key from the MCP dashboard
   - Create a `.env` file based on `.env.example`
   - Add your MCP API key to the `.env` file:
     ```
     MCP_API_KEY=your_mcp_api_key_here
     ```

4. Run the `main.py` script:
   ```
   python main.py
   ```
   
   The script will run indefinitely, making automated commits to your specified repositories at random intervals between `min_interval` and `max_interval` hours. Each run will generate between `min_commits` and `max_commits` commits.

   The script clones your repositories to a local `repos/` directory, makes the commits there, and pushes the changes to GitHub.

5. Let it run for a few days and then check your contribution graph on GitHub to see the generated activity! The longer you let it run, the more impressive the streak will look.

Remember, this is just a demo for educational purposes. Make sure to use it responsibly and don't violate GitHub's terms of service. Have fun hacking your contributions!

## Demo Results

After running the script for 5 days, here's the generated contribution activity:

![Contribution Graph Screenshot](contribution_graph.png)

As you can see, the script successfully generated at least 3 commits per day to the demo repositories, maintaining a 5-day streak.

## MCP Integration Demo

When MCP integration is enabled, the GitHub Contribution Hack generates more realistic and varied contributions. Here's a comparison of standard and MCP-generated content:

### Standard Generation

```python
# 2024-04-30 14:22:36
print('Hello')
```

### MCP-Enhanced Generation

```python
# Generated with MCP on 2024-04-30
def calculate_fibonacci(n):
    """
    Calculate the Fibonacci sequence up to n terms
    
    Args:
        n (int): Number of terms to generate
        
    Returns:
        list: Fibonacci sequence
    """
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# Generate and display the first 10 Fibonacci numbers
result = calculate_fibonacci(10)
print(f"First 10 Fibonacci numbers: {result}")
```

### Commit Messages Comparison

Standard: 
```
Automated contribution
```

MCP-Enhanced:
```
Add Fibonacci sequence calculator with documentation and example usage
```

## Trying It Yourself

To try the GitHub Contribution Hack yourself:

1. Generate a GitHub Personal Access Token with `repo` scope
2. Update `config.yml` with your token and target repositories
3. Obtain an MCP API key for enhanced content generation (optional)
4. Run `python main.py`

The script will run indefinitely, making commits at random intervals to your specified repositories. Customize the `min_commits`, `max_commits`, `min_interval` and `max_interval` settings to adjust the contribution frequency to your liking.

**Remember**: This tool is for educational purposes only. Make sure to use it responsibly and adhere to GitHub's terms of service. 