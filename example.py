#!/usr/bin/env python3
import os
import time
import random
import yaml
import argparse
from datetime import datetime
from pathlib import Path
import git
from dotenv import load_dotenv
import requests

def setup_example_config():
    """Create a minimal example configuration file."""
    config = {
        'repositories': ['username/example-repo'],  # Replace with your own repo
        'min_commits': 1,
        'max_commits': 3,
        'min_interval': 6,  # Hours
        'max_interval': 24,  # Hours
        'intelligent_patterns': {
            'enabled': True,
            'content_types': ['code', 'docs'],
            'time_distribution': 'poisson'
        },
        'notifications': {
            'enabled': False
        }
    }
    
    with open('example_config.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("Created example configuration in example_config.yml")
    print("Please edit it to include your repository name.")

def setup_example_env():
    """Create a sample .env file for the example."""
    if not os.path.exists('.env.example'):
        with open('.env.example', 'w') as f:
            f.write("# GitHub personal access token with repo scope\n")
            f.write("GITHUB_TOKEN=your_github_token_here\n")
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("# GitHub personal access token with repo scope\n")
            f.write("GITHUB_TOKEN=\n")
        
        print("Created .env file. Please edit it to add your GitHub token.")
    else:
        print(".env file already exists.")

def generate_content():
    """Generate simple random content for a commit."""
    content_types = [
        lambda: f"# Update {datetime.now()}\nprint('Hello, world!')",
        lambda: f"## Documentation Update\n\nUpdated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        lambda: f"// JavaScript update\nconsole.log('Updated: {datetime.now().strftime('%Y-%m-%d')}')",
        lambda: f"/* CSS Update */\n.updated {{ timestamp: '{datetime.now().strftime('%Y-%m-%d')}'; }}"
    ]
    
    commit_messages = [
        "Update documentation",
        "Add example code",
        "Fix formatting",
        "Update timestamp",
        "Maintain contribution streak"
    ]
    
    return random.choice(commit_messages), random.choice(content_types)()

def make_contribution(repo_path):
    """Make a simple contribution to the specified repository."""
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("Error: GitHub token not found in .env file")
        return False
    
    try:
        # Clone repository if it doesn't exist locally
        repo_dir = Path(f"./example_repos/{repo_path.split('/')[-1]}")
        
        if not repo_dir.exists():
            print(f"Cloning repository {repo_path}...")
            os.makedirs(repo_dir.parent, exist_ok=True)
            git_url = f"https://{token}@github.com/{repo_path}.git"
            repo = git.Repo.clone_from(git_url, repo_dir)
        else:
            print(f"Using existing repository at {repo_dir}...")
            repo = git.Repo(repo_dir)
            origin = repo.remotes.origin
            origin.pull()
        
        # Create or update a file
        commit_message, content = generate_content()
        filename = f"contribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = repo_dir / filename
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Stage, commit and push
        repo.git.add(file_path)
        repo.git.commit('-m', commit_message)
        
        # Push using credentials
        print(f"Pushing changes to {repo_path}...")
        repo.git.push('origin', 'main')
        
        print(f"Successfully made contribution to {repo_path}")
        return True
    
    except Exception as e:
        print(f"Error making contribution: {str(e)}")
        return False

def verify_contribution(repo_path):
    """Verify the contribution was made successfully."""
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("Error: GitHub token not found in .env file")
        return
    
    username, repo_name = repo_path.split('/')
    api_url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        commits = response.json()
        if commits:
            latest_commit = commits[0]
            print("\nVerification Results:")
            print(f"Latest commit: {latest_commit['commit']['message']}")
            print(f"Author: {latest_commit['commit']['author']['name']}")
            print(f"Date: {latest_commit['commit']['author']['date']}")
            print(f"URL: {latest_commit['html_url']}")
        else:
            print("No commits found in repository.")
    
    except Exception as e:
        print(f"Error verifying contribution: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='GitHub Contribution Hack Example')
    parser.add_argument('--setup', action='store_true', help='Setup example configuration files')
    parser.add_argument('--contribute', action='store_true', help='Make a test contribution')
    parser.add_argument('--repo', type=str, help='Repository to contribute to (username/repo)')
    parser.add_argument('--verify', action='store_true', help='Verify contributions were made')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_example_config()
        setup_example_env()
        return
    
    if args.contribute:
        repo_path = args.repo
        
        if not repo_path:
            # Try to get repo from config file
            if os.path.exists('example_config.yml'):
                with open('example_config.yml', 'r') as f:
                    config = yaml.safe_load(f)
                    repos = config.get('repositories', [])
                    if repos:
                        repo_path = repos[0]
        
        if not repo_path:
            print("Error: Please specify a repository with --repo username/repo")
            return
        
        success = make_contribution(repo_path)
        
        if success and args.verify:
            print("Waiting a moment for GitHub to process the commit...")
            time.sleep(3)
            verify_contribution(repo_path)
    
    elif args.verify:
        if not args.repo:
            print("Error: Please specify a repository with --repo username/repo")
            return
        
        verify_contribution(args.repo)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 