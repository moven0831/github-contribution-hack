# Stay in a Streak! GitHub Contribution Hack

This project aims to create a program that automatically makes contributions to a connected GitHub account, allowing the contribution graph to maintain a consistent streak.

## Features

- Automatically create commits and push them to GitHub on a regular schedule
- Configurable settings for commit frequency and repository selection
- Seamless integration with GitHub API for authentication and contribution tracking
- **Enhanced Security**: Encrypted credential storage and system keyring integration
- **Intelligent Patterns**: ML-powered commit messages and natural time distribution
- **Real-Time Monitoring**: Interactive dashboard with streak analytics and verification
- Cross-platform compatibility (Windows, macOS, Linux)

## Getting Started

### Prerequisites

- Python 3.x installed
- GitHub account with personal access token
- Git installed on your system
- [Optional] Node.js v18+ for advanced monitoring features

### Security Setup

Instead of manual .env configuration, run the security initialization:
```bash
python setup_security.py
```
This will guide you through:
1. Encrypting your GitHub token
2. Setting up system keyring integration
3. Configuring automatic credential rotation

### Intelligent Commit Configuration

Enable smart patterns in `config.yml`:
```yaml
intelligent_patterns:
  enabled: true
  content_types: [code, docs, config]
  time_distribution: poisson
```

### Monitoring Dashboard

Start the interactive analytics dashboard:
```bash
python main.py --monitor
```

Key monitoring features:
- Real-time contribution graph
- Streak success probability estimation
- Repository activity distribution
- Automated GitHub commit verification

## Advanced Features

### Security Recommendations
```bash
# Rotate credentials monthly
python setup_security.py --rotate

# Audit stored credentials
python setup_security.py --audit
```

### Pattern Customization
1. Collect historical commits in commit_patterns.json
2. Retrain the ML model:
```bash
python train_patterns.py --input commit_patterns.json
```

### Analytics Integration
View historical reports:
```bash
python analytics.py --report weekly-summary
```

Export monitoring data:
```bash
python analytics.py --export csv
```

Note: The monitoring dashboard requires additional dependencies:
```bash
pip install -r requirements-monitoring.txt
```

### Quick Start Demo

To quickly see the GitHub Contribution Hack in action:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/github-contribution-hack.git
   cd github-contribution-hack  
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your GitHub token:
   - Generate a GitHub Personal Access Token with `repo` scope at https://github.com/settings/tokens
   - Copy the `.env.example` file to `.env`:
     ```
     cp .env.example .env
     ```
   - Replace `your_github_token_here` in `.env` with your actual token

4. Run the demo:
   ```
   python main.py
   ```

The demo will start generating automated commits to the preconfigured public demo repositories. Check the `contribution_graph.png` in the `DEMO.md` file to see an example of the generated activity.

Note: The demo repositories are public and read-only. To use the tool with your own repositories, update the repository list in `config.yml`.

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/github-contribution-hack.git
   cd github-contribution-hack  
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your GitHub token:
   - Generate a GitHub Personal Access Token with `repo` scope at https://github.com/settings/tokens
   - Copy the `.env.example` file to `.env`:
     ```
     cp .env.example .env
     ```
   - Replace `your_github_token_here` in `.env` with your actual token

4. Run the demo:
   ```
   python main.py
   ```

The demo will start generating automated commits to the preconfigured public demo repositories. Check the `contribution_graph.png` in the `DEMO.md` file to see an example of the generated activity.

Note: The demo repositories are public and read-only. To use the tool with your own repositories, update the repository list in `config.yml`.
