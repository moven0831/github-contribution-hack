import os
import yaml
import random
import time
import subprocess
from datetime import datetime, timedelta
import git
import github
from dotenv import load_dotenv
import json
from analytics import ContributionAnalytics
from mcp_integration import MCPClient, get_mcp_client, get_session
import concurrent.futures
import functools
import tempfile
from pathlib import Path

# Add LRU cache for efficient function calls
from functools import lru_cache

class GitHubContributionHack:
    def __init__(self, config_path='config.yml'):
        """
        Initialize the GitHub Contribution Hack
        
        :param config_path: Path to the configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as config_file:
            self.config = yaml.safe_load(config_file)
        
        self._validate_environment()
        self._setup_secure_credentials()
        self._configure_repository_access()
        
        # Initialize HTTP session for better performance
        self.session = get_session()
        
        # Get repositories to contribute to
        self.repositories = self.config.get('repositories', [])
        if not self.repositories:
            raise ValueError("No repositories specified in config.yml")
        
        # Commit frequency settings
        self.min_commits = self.config.get('min_commits', 1)
        self.max_commits = self.config.get('max_commits', 3)
        
        # Interval settings (in hours)
        self.min_interval = self.config.get('min_interval', 12)
        self.max_interval = self.config.get('max_interval', 24)
        
        # Configure performance settings
        self.max_workers = self.config.get('performance', {}).get('max_workers', 4)
        self.parallel_repos = self.config.get('performance', {}).get('parallel_repos', True)
        
        # Use a local shared repo cache to avoid repeated cloning
        self.repo_cache_dir = Path(tempfile.gettempdir()) / 'github_contrib_cache'
        os.makedirs(self.repo_cache_dir, exist_ok=True)
        
        self.commit_pattern_model = self._load_commit_pattern_model()
        self.file_types = ['txt', 'md', 'py', 'js', 'json']
        self.analytics = ContributionAnalytics()
        self._setup_github_verification()
        
        # Initialize MCP client if MCP integration is enabled
        self.mcp_client = None
        if self.config.get('mcp_integration', {}).get('enabled', False):
            try:
                self.mcp_client = get_mcp_client()
                print("MCP integration enabled successfully")
            except Exception as e:
                print(f"Failed to initialize MCP integration: {str(e)}")
                print("Falling back to standard content generation")
    
    def _validate_environment(self):
        """Validate required environment setup"""
        if not os.path.exists('.env'):
            raise EnvironmentError(".env file missing - copy .env.example and configure credentials")
            
    def _setup_secure_credentials(self):
        """Securely load and manage GitHub credentials"""
        # Try loading from encrypted storage first
        self.github_token = self._get_encrypted_token()
        
        if not self.github_token:
            # Fallback to .env with user confirmation
            if os.getenv('GITHUB_TOKEN'):
                if self._prompt_for_encryption():
                    self._encrypt_and_store_token(os.getenv('GITHUB_TOKEN'))
                    self.github_token = os.getenv('GITHUB_TOKEN')
                else:
                    raise PermissionError("User declined secure storage setup")
            else:
                raise ValueError("No valid credentials found - run setup_security.py first")

    def _get_encrypted_token(self):
        """Retrieve encrypted token from secure storage"""
        try:
            # Use system keyring for secure storage
            import keyring
            encrypted_token = keyring.get_password('github_contribution', 'api_token')
            return self._decrypt_token(encrypted_token) if encrypted_token else None
        except Exception as e:
            print(f"Secure storage error: {str(e)}")
            return None

    def _encrypt_and_store_token(self, token):
        """Encrypt and securely store the token"""
        # Use Fernet symmetric encryption
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        encrypted_token = cipher_suite.encrypt(token.encode())
        
        # Store encrypted token in system keyring
        import keyring
        keyring.set_password('github_contribution', 'api_token', encrypted_token.decode())
        
        # Store encryption key in separate secure location
        self._store_encryption_key(key)

    def _prompt_for_encryption(self):
        """Get user confirmation for credential encryption"""
        print("Security recommendation: Store credentials in encrypted format")
        return input("Encrypt and store credentials securely? (y/n): ").lower() == 'y'

    def _load_commit_pattern_model(self):
        """Load ML model for commit pattern prediction"""
        try:
            import markovify
            with open("commit_patterns.json") as f:
                return markovify.Text.from_json(f.read())
        except Exception as e:
            print(f"Pattern model error: {str(e)}")
            return None

    def generate_random_content(self):
        """Generate context-aware commit content"""
        # Check if MCP integration is enabled and client is available
        if self.config.get('mcp_integration', {}).get('enabled', False) and self.mcp_client:
            return self._generate_mcp_content()
        elif random.random() < 0.3 and self.commit_pattern_model:
            # Generate ML-based commit message
            message = self.commit_pattern_model.make_sentence()
            content = self._generate_code_content() if random.random() < 0.4 else self._generate_doc_content()
        else:
            # Fallback to random content
            message, content = self._basic_content_generation()
            
        return message, content

    def _generate_code_content(self):
        """Generate simple code-like content"""
        languages = {
            'py': lambda: f"# {datetime.now()}\nprint('{random.choice(['Hello', 'World', 'Test'])}')",
            'js': lambda: f"// {datetime.now()}\nconsole.log('{random.choice(['Debug', 'Info', 'Data'])}')",
            'md': lambda: f"## Update {datetime.now()}\n- Item {random.randint(1,100)}",
            'json': lambda: json.dumps({"timestamp": str(datetime.now()), "value": random.random()})
        }
        ext = random.choice(self.file_types)
        return languages.get(ext, lambda: f"Content: {datetime.now()}")()

    def _generate_doc_content(self):
        """Generate simple document-like content"""
        # Implement document content generation logic here
        return f"Document content at {datetime.now()}"

    def _basic_content_generation(self):
        """Fallback to basic content generation"""
        commit_messages = [
            "Maintain contribution streak",
            "Daily code update",
            "Automated contribution",
            "Keeping the streak alive",
            "Consistency is key"
        ]
        
        return random.choice(commit_messages), f"Contribution at {datetime.now()}"
    
    def _generate_mcp_content(self):
        """Generate content using MCP integration"""
        try:
            # Select a language based on configuration or random choice
            language_weights = self.config.get('mcp_integration', {}).get('language_weights', {
                'python': 0.4, 
                'javascript': 0.3, 
                'markdown': 0.2,
                'text': 0.1
            })
            
            # Choose language based on weights
            languages = list(language_weights.keys())
            weights = list(language_weights.values())
            language = random.choices(languages, weights=weights, k=1)[0]
            
            # Generate code using MCP
            context = {
                "purpose": "github-contribution",
                "complexity": self.config.get('mcp_integration', {}).get('complexity', 'low'),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            generated_code = self.mcp_client.generate_code(language, context)
            
            # Get file changes metadata for commit message generation
            changes = [{
                "file_type": language,
                "size": len(generated_code),
                "operation": "modify"
            }]
            
            # Generate commit message
            current_repo = random.choice(self.repositories)
            commit_message = self.mcp_client.generate_commit_message(changes, current_repo)
            
            return commit_message, generated_code
            
        except Exception as e:
            print(f"MCP content generation failed: {str(e)}")
            # Fall back to basic content generation
            return self._basic_content_generation()

    @lru_cache(maxsize=32)
    def _get_cached_repo_info(self, repo_name):
        """Get cached repository information"""
        return self.g.get_repo(repo_name)

    def make_contributions(self):
        """
        Make automated contributions to selected repositories
        """
        if self.parallel_repos and len(self.repositories) > 1:
            # Use parallel processing for multiple repositories
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all repo tasks to the executor
                futures = {
                    executor.submit(self._process_single_repo, repo_name): repo_name 
                    for repo_name in self.repositories
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(futures):
                    repo_name = futures[future]
                    try:
                        result = future.result()
                        print(f"Successfully processed repository: {repo_name}")
                    except Exception as e:
                        print(f"Error processing repository {repo_name}: {str(e)}")
        else:
            # Process repositories sequentially
            for repo_name in self.repositories:
                try:
                    self._process_single_repo(repo_name)
                    print(f"Successfully processed repository: {repo_name}")
                except Exception as e:
                    print(f"Error processing repository {repo_name}: {str(e)}")
    
    def _process_single_repo(self, repo_name):
        """Process a single repository for contributions"""
        try:
            # Get repo info (uses LRU cache)
            repo = self._get_cached_repo_info(repo_name)
            repo_url = f"https://{self.github_token}@github.com/{repo_name}.git"
            
            # Create local directory if not exists
            local_path = os.path.join('repos', repo_name.replace('/', '_'))
            os.makedirs(local_path, exist_ok=True)
            
            # Use the cached clone if available, otherwise clone new
            cache_key = repo_name.replace('/', '_')
            cache_path = self.repo_cache_dir / cache_key
            
            if not os.path.exists(os.path.join(local_path, '.git')):
                if cache_path.exists() and (cache_path / '.git').exists():
                    # Copy from cache instead of clone
                    import shutil
                    shutil.copytree(cache_path, local_path, dirs_exist_ok=True)
                    repo_obj = git.Repo(local_path)
                    repo_obj.remotes.origin.pull()
                else:
                    # Clone and cache
                    repo_obj = git.Repo.clone_from(repo_url, local_path)
                    # Cache this clone for future use if not already cached
                    if not cache_path.exists():
                        shutil.copytree(local_path, cache_path, dirs_exist_ok=True)
            else:
                # Just pull latest changes
                repo_obj = git.Repo(local_path)
                repo_obj.remotes.origin.pull()
            
            # Make random number of commits
            num_commits = random.randint(self.min_commits, self.max_commits)
            commits_made = []
            total_lines = 0
            file_ext = None
            
            # Pre-generate all content to avoid API rate limits during commit loop
            commit_contents = []
            for _ in range(num_commits):
                commit_message, content = self.generate_random_content()
                commit_contents.append((commit_message, content))
            
            # Process all commits
            for commit_message, content in commit_contents:
                commits_made.append(commit_message)
                total_lines += len(content.splitlines())
                if file_ext is None:
                    file_ext = content.split('.')[-1] if '.' in content else 'txt'
                self._make_single_commit(local_path, commit_message, content)
            
            self.analytics.log_contribution(
                repo_name, 
                commit_count=len(commits_made),
                lines_changed=total_lines,
                file_type=file_ext
            )
            
            return {
                'commits': len(commits_made),
                'lines': total_lines,
                'file_type': file_ext
            }
            
        except Exception as e:
            print(f"Error processing repository {repo_name}: {str(e)}")
            raise

    def _make_single_commit(self, repo_path, commit_message, content):
        """
        Make a single commit to the repository
        
        :param repo_path: Local path to the repository
        :param commit_message: Commit message
        :param content: Commit content
        """
        repo = git.Repo(repo_path)
        
        # Determine file extension based on content
        file_ext = "txt"  # Default fallback
        
        # MCP integration: Detect file type for better filename
        if self.config.get('mcp_integration', {}).get('enabled', False):
            if content.startswith("# ") or "def " in content or "import " in content:
                file_ext = "py"
            elif content.startswith("//") or "function " in content or "const " in content:
                file_ext = "js"
            elif content.startswith("# ") and "## " in content:
                file_ext = "md"
            elif content.startswith("{") or content.startswith("["):
                file_ext = "json"
        
        # Create a dummy file or modify an existing one
        file_path = os.path.join(repo_path, f'contribution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{file_ext}')
        
        # Write content to file
        with open(file_path, 'w') as f:
            f.write(content)

        # Check if commit splitting is enabled
        if self.config.get('split_commits', {}).get('enabled', False):
            # Read the file contents
            with open(file_path, 'r') as f:
                lines = f.readlines()

            max_lines = self.config['split_commits']['max_lines_per_commit']
            prefix = self.config['split_commits']['message_prefix']

            # Split the lines into chunks
            line_chunks = [lines[i:i+max_lines] for i in range(0, len(lines), max_lines)]

            # Make a separate commit for each chunk
            for i, chunk in enumerate(line_chunks):
                # Write the chunk to the file
                with open(file_path, 'w') as f:
                    f.writelines(chunk)

                # Stage and commit changes
                repo.git.add(file_path)
                repo.git.commit('-m', f"{prefix} {i+1}/{len(line_chunks)}")

            # Push changes
            repo.git.push('origin', 'main')

        else:
            # Stage and commit changes
            repo.git.add(file_path)
            repo.git.commit('-m', commit_message)
            
            # Push changes
            repo.git.push('origin', 'main')

    def _verify_github_activity(self, repo_name, expected_commits):
        """Verify commits appear on GitHub"""
        from github import Github
        g = Github(self.github_token)
        repo = g.get_repo(repo_name)
        
        actual_commits = list(repo.get_commits(
            since=datetime.now() - timedelta(hours=1)
        ))
        
        if len(actual_commits) < len(expected_commits):
            print(f"[WARNING] Missing commits on {repo_name} - " 
                  f"Expected {len(expected_commits)}, Found {len(actual_commits)}")
            self.analytics.log_verification_issue(repo_name)

    def start_monitoring(self):
        """Start real-time monitoring dashboard"""
        from threading import Thread
        Thread(target=self._monitoring_loop, daemon=True).start()

    def _monitoring_loop(self):
        """Continuous monitoring updates"""
        while True:
            self.analytics.generate_report()
            time.sleep(300)  # Update every 5 minutes

def main():
    hack = GitHubContributionHack()
    hack._schedule_commits()

if __name__ == '__main__':
    main() 