#!/usr/bin/env python3
"""
Security setup script for GitHub Contribution Hack
Handles secure credential setup, encryption, and rotation.
"""

import os
import sys
import argparse
import getpass
import uuid
import datetime
import logging
from typing import Optional
from pathlib import Path
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('security_setup')

# Try to import optional dependencies
try:
    import keyring
    import dotenv
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    import base64
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


class SecuritySetup:
    """Handles security setup for GitHub Contribution Hack"""
    
    ENV_FILE = '.env'
    KEYRING_SERVICE = 'github_contribution'
    KEYRING_USERNAME = 'api_token'
    KEY_STORAGE_FILE = '.key_info'
    
    def __init__(self):
        """Initialize security setup"""
        self.check_dependencies()
        self.load_env()
    
    def check_dependencies(self):
        """Check that required dependencies are installed"""
        if not DEPENDENCIES_AVAILABLE:
            logger.error("Required security dependencies not available")
            print("\n⛔ Security dependencies not installed. Installing now...")
            self.install_dependencies()
    
    def install_dependencies(self):
        """Install required dependencies"""
        try:
            import subprocess
            print("Installing required packages: keyring, python-dotenv, cryptography")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "keyring>=25.0.0", "python-dotenv>=1.0.0", "cryptography>=39.0.0"
            ])
            print("✅ Dependencies installed successfully")
            
            # Reload modules
            import importlib
            import site
            importlib.reload(site)
            
            global keyring, dotenv, Fernet, PBKDF2HMAC, hashes, default_backend, base64
            import keyring
            import dotenv
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            import base64
            
            global DEPENDENCIES_AVAILABLE
            DEPENDENCIES_AVAILABLE = True
        
        except Exception as e:
            logger.error(f"Failed to install dependencies: {str(e)}")
            print(f"\n⛔ Failed to install required packages: {str(e)}")
            print("Please install manually: pip install keyring python-dotenv cryptography")
            sys.exit(1)
    
    def load_env(self):
        """Load environment variables from .env file"""
        try:
            dotenv.load_dotenv()
        except Exception as e:
            logger.warning(f"Could not load .env file: {str(e)}")
    
    def setup_initial(self):
        """Set up initial security configuration"""
        print("\n🔐 GitHub Contribution Hack - Security Setup\n")
        
        # Check if GitHub token exists in environment
        github_token = os.getenv('GITHUB_TOKEN')
        
        if github_token:
            print("ℹ️  GitHub token found in environment")
            use_existing = input("Use existing token from environment? (y/n): ").lower() == 'y'
            
            if not use_existing:
                github_token = self.prompt_for_token()
        else:
            print("No GitHub token found in environment")
            github_token = self.prompt_for_token()
        
        # Save token to .env file as a backup
        self.update_env_file(github_token)
        
        # Set up encryption and keyring
        use_keyring = input("Use system keyring for secure storage? (recommended) (y/n): ").lower() == 'y'
        
        if use_keyring:
            self.setup_keyring(github_token)
            print("\n✅ Security setup complete!")
            print("Credentials are now securely stored in your system keyring and encrypted")
        else:
            print("\n⚠️  Using .env file only (less secure)")
            print("Your credentials will be stored in the .env file")
            print("✅ Basic setup complete")
    
    def prompt_for_token(self) -> str:
        """Prompt user for GitHub token"""
        print("\nTo create a new GitHub token:")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Click 'Generate new token'")
        print("3. Give it a name like 'GitHub Contribution Hack'")
        print("4. Select scopes: 'repo' and 'workflow'")
        print("5. Click 'Generate token'")
        print("6. Copy the token value\n")
        
        return getpass.getpass("Enter your GitHub token: ")
    
    def update_env_file(self, github_token: str):
        """Update .env file with GitHub token"""
        try:
            env_path = Path(self.ENV_FILE)
            
            # Read existing .env content if it exists
            if env_path.exists():
                env_content = env_path.read_text()
                # Replace existing token or add new one
                if 'GITHUB_TOKEN=' in env_content:
                    env_content = self.replace_env_var(env_content, 'GITHUB_TOKEN', github_token)
                else:
                    env_content += f"\nGITHUB_TOKEN={github_token}\n"
            else:
                # Create new .env file
                env_content = f"GITHUB_TOKEN={github_token}\n"
            
            # Write updated content
            env_path.write_text(env_content)
            os.chmod(env_path, 0o600)  # Set secure permissions
            
            logger.info("Updated .env file with GitHub token")
            print("✅ Updated .env file with GitHub token")
        
        except Exception as e:
            logger.error(f"Failed to update .env file: {str(e)}")
            print(f"⛔ Failed to update .env file: {str(e)}")
    
    def replace_env_var(self, content: str, var_name: str, new_value: str) -> str:
        """Replace environment variable in content"""
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.startswith(f"{var_name}="):
                updated_lines.append(f"{var_name}={new_value}")
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)
    
    def setup_keyring(self, github_token: str):
        """Set up keyring with encrypted token"""
        try:
            # Generate encryption key
            key = Fernet.generate_key()
            cipher_suite = Fernet(key)
            
            # Encrypt token
            encrypted_token = cipher_suite.encrypt(github_token.encode()).decode()
            
            # Store in keyring
            keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME, encrypted_token)
            
            # Save key info (but not the key itself) for tracking
            self.save_key_info(key)
            
            logger.info("Token encrypted and stored in keyring")
            print("✅ Token encrypted and stored in system keyring")
        
        except Exception as e:
            logger.error(f"Failed to set up keyring: {str(e)}")
            print(f"⛔ Failed to set up keyring: {str(e)}")
            print("Token saved to .env file only")
    
    def save_key_info(self, key: bytes):
        """Save key metadata (not the key itself) for tracking"""
        try:
            # Generate a reference ID from the key (not the actual key)
            key_hash = self.hash_key(key)
            
            key_info = {
                "key_id": key_hash,
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rotation_due": (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            # Save the actual key securely
            self.store_encryption_key(key)
            
            # Save key metadata
            with open(self.KEY_STORAGE_FILE, 'w') as f:
                json.dump(key_info, f)
                
            os.chmod(self.KEY_STORAGE_FILE, 0o600)  # Set secure permissions
            
            logger.info(f"Saved key info with ID {key_hash}")
        
        except Exception as e:
            logger.error(f"Failed to save key info: {str(e)}")
    
    def hash_key(self, key: bytes) -> str:
        """Create a hash of the key for reference"""
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key)
        return digest.finalize().hex()[:8]
    
    def store_encryption_key(self, key: bytes):
        """Store encryption key securely"""
        try:
            # Use keyring to store the key securely
            keyring.set_password(self.KEYRING_SERVICE, 'encryption_key', key.decode())
            logger.info("Stored encryption key in keyring")
        except Exception as e:
            logger.error(f"Failed to store encryption key: {str(e)}")
            # Fallback to file-based storage in secure location
            self.store_key_in_file(key)
    
    def store_key_in_file(self, key: bytes):
        """Fallback for storing encryption key in a secure file"""
        secure_dir = os.path.join(str(Path.home()), '.config', 'gh-contrib-hack')
        os.makedirs(secure_dir, exist_ok=True)
        key_file = os.path.join(secure_dir, '.encryption_key')
        
        with open(key_file, 'wb') as f:
            f.write(key)
        
        os.chmod(key_file, 0o600)  # Set secure permissions
        logger.info(f"Stored encryption key in {key_file}")
    
    def rotate_credentials(self):
        """Rotate GitHub token and encryption keys"""
        print("\n🔄 Credential Rotation\n")
        
        # Prompt for new token
        github_token = self.prompt_for_token()
        
        # Update .env file
        self.update_env_file(github_token)
        
        # Generate new encryption key
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        
        # Encrypt token
        encrypted_token = cipher_suite.encrypt(github_token.encode()).decode()
        
        # Update keyring
        try:
            keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME, encrypted_token)
            self.save_key_info(key)
            print("✅ Credentials rotated successfully")
        except Exception as e:
            logger.error(f"Failed to update keyring: {str(e)}")
            print(f"⛔ Failed to update keyring: {str(e)}")
            print("Token saved to .env file only")
    
    def audit_security(self):
        """Audit current security configuration"""
        print("\n🔍 Security Audit\n")
        
        issues = []
        recommendations = []
        
        # Check for .env file
        if os.path.exists(self.ENV_FILE):
            print("✅ .env file exists")
            
            # Check permissions
            try:
                env_perms = oct(os.stat(self.ENV_FILE).st_mode)[-3:]
                if env_perms != '600':
                    issues.append(f".env file has insecure permissions: {env_perms}")
                    recommendations.append("Set .env file permissions to 600: chmod 600 .env")
                else:
                    print("✅ .env file has secure permissions")
            except Exception:
                issues.append("Could not check .env file permissions")
        else:
            issues.append(".env file not found")
            recommendations.append("Run setup_security.py to configure credentials")
        
        # Check keyring configuration
        try:
            encrypted_token = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            if encrypted_token:
                print("✅ Encrypted token found in keyring")
            else:
                issues.append("No encrypted token in keyring")
                recommendations.append("Run setup_security.py to set up keyring storage")
        except Exception as e:
            issues.append(f"Keyring error: {str(e)}")
            recommendations.append("Reinstall keyring with pip install --upgrade keyring")
        
        # Check key rotation
        try:
            if os.path.exists(self.KEY_STORAGE_FILE):
                with open(self.KEY_STORAGE_FILE, 'r') as f:
                    key_info = json.load(f)
                
                rotation_due = datetime.datetime.strptime(key_info['rotation_due'], "%Y-%m-%d")
                today = datetime.datetime.now()
                
                if today > rotation_due:
                    days_overdue = (today - rotation_due).days
                    issues.append(f"Encryption key rotation overdue by {days_overdue} days")
                    recommendations.append("Run setup_security.py --rotate to rotate credentials")
                else:
                    days_left = (rotation_due - today).days
                    print(f"✅ Key rotation due in {days_left} days")
            else:
                issues.append("No key tracking information found")
                recommendations.append("Run setup_security.py to set up secure key tracking")
        except Exception as e:
            issues.append(f"Could not check key rotation status: {str(e)}")
        
        # Print summary
        print("\nSecurity Audit Summary:")
        
        if issues:
            print("\n⚠️  Issues Found:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ No security issues found")
        
        if recommendations:
            print("\n🔧 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        return len(issues) == 0

    def renew_token(self):
        """Renew GitHub token without changing encryption keys"""
        print("\n🔄 GitHub Token Renewal\n")
        
        # Prompt for new token
        github_token = self.prompt_for_token()
        
        # Update .env file
        self.update_env_file(github_token)
        
        # Get existing encryption key from keyring
        try:
            encryption_key = keyring.get_password(self.KEYRING_SERVICE, 'encryption_key')
            if not encryption_key:
                print("⚠️  No existing encryption key found, generating new one")
                encryption_key = Fernet.generate_key()
            else:
                encryption_key = encryption_key.encode()
        except Exception:
            print("⚠️  Could not retrieve encryption key, generating new one")
            encryption_key = Fernet.generate_key()
        
        # Encrypt token
        cipher_suite = Fernet(encryption_key)
        encrypted_token = cipher_suite.encrypt(github_token.encode()).decode()
        
        # Update keyring
        try:
            keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME, encrypted_token)
            print("✅ GitHub token renewed successfully")
        except Exception as e:
            logger.error(f"Failed to update keyring: {str(e)}")
            print(f"⛔ Failed to update keyring: {str(e)}")
            print("Token saved to .env file only")


def main():
    """Main entry point for the security setup script"""
    parser = argparse.ArgumentParser(description="Security setup for GitHub Contribution Hack")
    
    # Add exclusive group for operation modes
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--rotate", action="store_true", help="Rotate credentials and encryption keys")
    group.add_argument("--audit", action="store_true", help="Audit security configuration")
    group.add_argument("--renew", action="store_true", help="Renew GitHub token only")
    
    args = parser.parse_args()
    
    # Create security setup instance
    setup = SecuritySetup()
    
    if args.rotate:
        setup.rotate_credentials()
    elif args.audit:
        setup.audit_security()
    elif args.renew:
        setup.renew_token()
    else:
        # Default is to run initial setup
        setup.setup_initial()


if __name__ == "__main__":
    main() 