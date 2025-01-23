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
