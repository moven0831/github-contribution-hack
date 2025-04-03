"""
Unit tests for security components in main.py
"""
import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, Mock, mock_open
import pytest

# Add parent directory to path so we can import modules
sys.path.insert(0, '.')

# Import required modules for testing
from main import GitHubContributionHack

class TestSecurityComponents(unittest.TestCase):
    """Test the security-related methods in GitHubContributionHack"""
    
    def setUp(self):
        """Set up test environment"""
        # Create environment for tests
        self.original_environ = os.environ.copy()
        os.environ["GITHUB_TOKEN"] = "test_token"
        
        # Create a temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
        with open(self.temp_config.name, 'w') as f:
            f.write("""
            repositories:
              - test/repo1
            min_commits: 1
            max_commits: 3
            """)
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_environ)
        
        # Remove temporary config file
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._encrypt_and_store_token')
    @patch('main.GitHubContributionHack._get_encrypted_token')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    def test_secure_credentials_setup_with_env_var(self, mock_pattern, mock_analytics, 
                                                  mock_verification, mock_repo_access, 
                                                  mock_get_token, mock_encrypt, mock_validate):
        """Test secure credentials setup with env var"""
        # Setup mocks
        mock_get_token.return_value = None  # No encrypted token
        mock_encrypt.return_value = None
        
        # Create instance with mocked _prompt_for_encryption
        with patch('main.GitHubContributionHack._prompt_for_encryption', return_value=True):
            instance = GitHubContributionHack(config_path=self.temp_config.name)
            
            # Should have called encrypt_and_store
            mock_encrypt.assert_called_once_with("test_token")
            
            # Should have set the github_token
            self.assertEqual(instance.github_token, "test_token")
    
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    @patch('main.GitHubContributionHack._prompt_for_encryption')
    @patch('main.GitHubContributionHack._get_encrypted_token')
    def test_secure_credentials_setup_decline_encryption(self, mock_get_token, mock_prompt,
                                                        mock_pattern, mock_analytics, mock_verification,
                                                        mock_repo_access, mock_validate):
        """Test secure credentials setup when user declines encryption"""
        # Setup mocks
        mock_get_token.return_value = None  # No encrypted token
        mock_prompt.return_value = False  # User declines encryption
        
        # Should raise PermissionError
        with self.assertRaises(PermissionError):
            GitHubContributionHack(config_path=self.temp_config.name)
    
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    def test_secure_credentials_setup_with_encrypted_token(self, mock_pattern, mock_analytics,
                                                         mock_verification, mock_repo_access,
                                                         mock_validate):
        """Test secure credentials setup with existing encrypted token"""
        # Create instance with mocked _get_encrypted_token
        with patch('main.GitHubContributionHack._get_encrypted_token', return_value="decrypted_token"):
            instance = GitHubContributionHack(config_path=self.temp_config.name)
            
            # Should have set the github_token to the decrypted value
            self.assertEqual(instance.github_token, "decrypted_token")
    
    @patch('keyring.get_password')
    def test_get_encrypted_token_success(self, mock_get_password):
        """Test successful retrieval of encrypted token"""
        # Setup mock
        mock_get_password.return_value = "encrypted_token"
        
        # Create instance with mocked _decrypt_token
        with patch('main.GitHubContributionHack._decrypt_token', return_value="decrypted_token"):
            # Directly test the method on a mocked instance
            instance = MagicMock(spec=GitHubContributionHack)
            instance._decrypt_token.return_value = "decrypted_token"
            
            # Call the method
            from main import GitHubContributionHack
            result = GitHubContributionHack._get_encrypted_token(instance)
            
            # Verify result
            self.assertEqual(result, "decrypted_token")
            mock_get_password.assert_called_once_with('github_contribution', 'api_token')
    
    @patch('keyring.get_password')
    def test_get_encrypted_token_not_found(self, mock_get_password):
        """Test retrieval when encrypted token not found"""
        # Setup mock
        mock_get_password.return_value = None
        
        # Directly test the method on a mocked instance
        instance = MagicMock(spec=GitHubContributionHack)
        
        # Call the method
        from main import GitHubContributionHack
        result = GitHubContributionHack._get_encrypted_token(instance)
        
        # Verify result
        self.assertIsNone(result)
        mock_get_password.assert_called_once_with('github_contribution', 'api_token')
    
    @patch('keyring.get_password')
    def test_get_encrypted_token_exception(self, mock_get_password):
        """Test handling of exceptions during token retrieval"""
        # Setup mock to raise an exception
        mock_get_password.side_effect = Exception("Keyring error")
        
        # Directly test the method on a mocked instance
        instance = MagicMock(spec=GitHubContributionHack)
        
        # Call the method
        from main import GitHubContributionHack
        result = GitHubContributionHack._get_encrypted_token(instance)
        
        # Verify result
        self.assertIsNone(result)
        mock_get_password.assert_called_once_with('github_contribution', 'api_token')
    
    @patch('cryptography.fernet.Fernet.generate_key')
    @patch('cryptography.fernet.Fernet')
    @patch('keyring.set_password')
    def test_encrypt_and_store_token(self, mock_set_password, mock_fernet, mock_generate_key):
        """Test token encryption and storage"""
        # Setup mocks
        mock_generate_key.return_value = b'test_key'
        mock_cipher = Mock()
        mock_cipher.encrypt.return_value = b'encrypted_data'
        mock_fernet.return_value = mock_cipher
        
        # Directly test the method on a mocked instance
        instance = MagicMock(spec=GitHubContributionHack)
        instance._store_encryption_key = Mock()
        
        # Call the method
        from main import GitHubContributionHack
        GitHubContributionHack._encrypt_and_store_token(instance, "test_token")
        
        # Verify encryption and storage
        mock_fernet.assert_called_once_with(b'test_key')
        mock_cipher.encrypt.assert_called_once_with(b'test_token')
        mock_set_password.assert_called_once_with('github_contribution', 'api_token', 'encrypted_data')
        instance._store_encryption_key.assert_called_once_with(b'test_key')
    
    def test_prompt_for_encryption(self):
        """Test user prompt for encryption"""
        # Test with user input 'y'
        with patch('builtins.input', return_value='y'):
            instance = MagicMock(spec=GitHubContributionHack)
            from main import GitHubContributionHack
            result = GitHubContributionHack._prompt_for_encryption(instance)
            self.assertTrue(result)
        
        # Test with user input 'n'
        with patch('builtins.input', return_value='n'):
            instance = MagicMock(spec=GitHubContributionHack)
            from main import GitHubContributionHack
            result = GitHubContributionHack._prompt_for_encryption(instance)
            self.assertFalse(result)
        
        # Test with user input 'yes' (should be False since not exactly 'y')
        with patch('builtins.input', return_value='yes'):
            instance = MagicMock(spec=GitHubContributionHack)
            from main import GitHubContributionHack
            result = GitHubContributionHack._prompt_for_encryption(instance)
            self.assertFalse(result)
    
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._setup_secure_credentials')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    def test_validate_environment_missing_env_file(self, mock_pattern, mock_analytics,
                                                 mock_verification, mock_repo_access,
                                                 mock_credentials, mock_validate):
        """Test environment validation with missing .env file"""
        # Mock the _validate_environment method to test it separately
        mock_validate.side_effect = GitHubContributionHack._validate_environment
        
        # Mock os.path.exists to return False for .env
        with patch('os.path.exists', return_value=False):
            # Should raise EnvironmentError
            with self.assertRaises(EnvironmentError):
                GitHubContributionHack(config_path=self.temp_config.name)

if __name__ == "__main__":
    unittest.main() 