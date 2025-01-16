# Stay in a Streak! GitHub Contribution Hack

This project aims to create a program that automatically makes contributions to a connected GitHub account, allowing the contribution graph to maintain a consistent streak.

## Features

- Automatically create commits and push them to GitHub on a regular schedule
- Configurable settings for commit frequency and repository selection
- Seamless integration with GitHub API for authentication and contribution tracking
- Cross-platform compatibility (Windows, macOS, Linux)

## Getting Started

### Prerequisites

- Python 3.x installed
- GitHub account with personal access token
- Git installed on your system

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/github-contribution-hack.git
   cd github-contribution-hack
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure GitHub Access Token
   - Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
   - Generate a new token with `repo` scope
   - Copy the token and replace `YOUR_GITHUB_ACCESS_TOKEN` in `config.yml`

5. Configure Repositories
   - Edit `config.yml` and replace the repository list with your own repositories
   - Example: `yourusername/your-repository`

### Usage

Run the program using the following command:
```
python main.py
```

The program will start making automated contributions to your selected GitHub repositories based on the configured settings.

### Configuration Options

In `config.yml`, you can customize:
- `github_token`: Your GitHub personal access token
- `repositories`: List of repositories to contribute to
- `min_commits` and `max_commits`: Range of commits per repository
- `min_interval` and `max_interval`: Time between contribution runs (in hours)

## Security Warning

🚨 **IMPORTANT**: 
- Never commit your actual GitHub token to version control
- Keep your `config.yml` private
- Use environment variables or secure token management for production use

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## Disclaimer

This tool is for educational purposes. Use responsibly and in compliance with GitHub's terms of service.
