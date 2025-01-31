import os
import yaml
import random
import time
import subprocess
from datetime import datetime, timedelta
import git
import github
from dotenv import load_dotenv

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

    def generate_random_content(self):
        """
        Generate random content for commits
        
        :return: Random commit message and content
        """
        commit_messages = [
            "Maintain contribution streak",
            "Daily code update",
            "Automated contribution",
            "Keeping the streak alive",
            "Consistency is key"
        ]
        
        return random.choice(commit_messages), f"Contribution at {datetime.now()}"
    
    def make_contributions(self):
        """
        Make automated contributions to selected repositories
        """
        for repo_name in self.repositories:
            try:
                # Clone or update repository
                repo = self.g.get_repo(repo_name)
                repo_url = f"https://{self.github_token}@github.com/{repo_name}.git"
                
                # Create local directory if not exists
                local_path = os.path.join('repos', repo_name.replace('/', '_'))
                os.makedirs(local_path, exist_ok=True)
                
                # Clone or pull repository
                if not os.path.exists(os.path.join(local_path, '.git')):
                    git.Repo.clone_from(repo_url, local_path)
                else:
                    repo_obj = git.Repo(local_path)
                    repo_obj.remotes.origin.pull()
                
                # Make random number of commits
                num_commits = random.randint(self.min_commits, self.max_commits)
                for _ in range(num_commits):
                    self._make_single_commit(local_path)
                
                print(f"Contributions made to {repo_name}")
            
            except Exception as e:
                print(f"Error contributing to {repo_name}: {e}")
    
    def _make_single_commit(self, repo_path):
        """
        Make a single commit to the repository
        
        :param repo_path: Local path to the repository
        """
        repo = git.Repo(repo_path)
        
        # Create a dummy file or modify an existing one
        file_path = os.path.join(repo_path, f'contribution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
        # Generate commit content
        commit_message, content = self.generate_random_content()
        
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
    
    def run(self):
        """
        Run the contribution hack continuously
        """
        while True:
            # Make contributions
            self.make_contributions()
            
            # Sleep for a random interval
            sleep_hours = random.uniform(self.min_interval, self.max_interval)
            print(f"Sleeping for {sleep_hours:.2f} hours")
            time.sleep(sleep_hours * 3600)

def main():
    hack = GitHubContributionHack()
    hack.run()

if __name__ == '__main__':
    main() 