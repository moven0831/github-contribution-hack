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
    
    @patch('main.GitHubContributionHack.__init__', return_value=None)
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._encrypt_and_store_token')
    @patch('main.GitHubContributionHack._get_encrypted_token')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    def test_secure_credentials_setup_with_env_var(self, mock_pattern, mock_analytics, 
                                                 mock_get_token, mock_encrypt, mock_validate, mock_init):
        """Test secure credentials setup with env var"""
        # Setup mocks
        mock_get_token.return_value = None  # No encrypted token
        mock_encrypt.return_value = None
        
        # Create instance and directly call the method to test
        instance = GitHubContributionHack()
        
        # Manually call and test the method 
        with patch('main.GitHubContributionHack._prompt_for_encryption', return_value=True):
            instance._setup_secure_credentials()
                
            # Should have called encrypt_and_store
            mock_encrypt.assert_called_once_with("test_token")
                
            # Should have set the github_token
            self.assertEqual(instance.github_token, "test_token")
    
    @patch('main.GitHubContributionHack.__init__', return_value=None)
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    @patch('main.GitHubContributionHack._prompt_for_encryption')
    @patch('main.GitHubContributionHack._get_encrypted_token')
    def test_secure_credentials_setup_decline_encryption(self, mock_get_token, mock_prompt,
                                                        mock_pattern, mock_analytics, 
                                                        mock_validate, mock_init):
        """Test secure credentials setup when user declines encryption"""
        # Setup mocks
        mock_get_token.return_value = None  # No encrypted token
        mock_prompt.return_value = False  # User declines encryption
        
        # Create instance and directly call the method to test
        instance = GitHubContributionHack()
        
        # Should raise PermissionError when called directly
        with self.assertRaises(PermissionError):
            instance._setup_secure_credentials()
    
    @patch('main.GitHubContributionHack.__init__', return_value=None)
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    def test_secure_credentials_setup_with_encrypted_token(self, mock_pattern, mock_analytics,
                                                         mock_validate, mock_init):
        """Test secure credentials setup with existing encrypted token"""
        # Create instance and directly call the method to test
        instance = GitHubContributionHack()
        
        # Patch the _get_encrypted_token method to return a token
        with patch('main.GitHubContributionHack._get_encrypted_token', return_value="decrypted_token"):
            instance._setup_secure_credentials()
                
            # Should have set the github_token to the decrypted value
            self.assertEqual(instance.github_token, "decrypted_token")
    
    @patch('keyring.get_password')
    def test_get_encrypted_token_success(self, mock_get_password):
        """Test successful retrieval of encrypted token"""
        # Setup mock
        mock_get_password.return_value = "encrypted_token"
        
        # Create an instance for testing
        instance = MagicMock()
        instance._decrypt_token.return_value = "decrypted_token"
        
        # Call the method
        result = GitHubContributionHack._get_encrypted_token(instance)
        
        # Verify result and mock calls
        mock_get_password.assert_called_once_with('github_contribution', 'api_token')
        instance._decrypt_token.assert_called_once_with("encrypted_token")
        self.assertEqual(result, "decrypted_token")
    
    @patch('keyring.get_password')
    def test_get_encrypted_token_not_found(self, mock_get_password):
        """Test retrieval when encrypted token not found"""
        # Setup mock
        mock_get_password.return_value = None
        
        # Create a mock instance
        instance = MagicMock()
        
        # Call the method
        result = GitHubContributionHack._get_encrypted_token(instance)
        
        # Verify result
        self.assertIsNone(result)
        mock_get_password.assert_called_once_with('github_contribution', 'api_token')
    
    @patch('keyring.get_password')
    def test_get_encrypted_token_exception(self, mock_get_password):
        """Test handling of exceptions during token retrieval"""
        # Setup mock to raise exception
        mock_get_password.side_effect = Exception("Keyring error")
        
        # Create a mock instance
        instance = MagicMock()
        
        # Call the method
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
        
        # Create a mock instance
        instance = MagicMock()
        instance._store_encryption_key = Mock()
        
        # Call the method
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
            # Create a mock instance
            instance = MagicMock()
            
            # Call the method
            result = GitHubContributionHack._prompt_for_encryption(instance)
            
            # Verify result
            self.assertTrue(result)
        
        # Test with user input 'n'
        with patch('builtins.input', return_value='n'):
            # Create a mock instance
            instance = MagicMock()
            
            # Call the method
            result = GitHubContributionHack._prompt_for_encryption(instance)
            
            # Verify result
            self.assertFalse(result)
        
        # Test with user input 'yes' (should be False since not exactly 'y')
        with patch('builtins.input', return_value='yes'):
            # Create a mock instance
            instance = MagicMock()
            
            # Call the method
            result = GitHubContributionHack._prompt_for_encryption(instance)
            
            # Verify result
            self.assertFalse(result)
    
    @patch('main.GitHubContributionHack.__init__', return_value=None)
    @patch('main.GitHubContributionHack._setup_secure_credentials')
    @patch('main.ContributionAnalytics')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    def test_validate_environment_missing_env_file(self, mock_pattern, mock_analytics,
                                                 mock_credentials, mock_init):
        """Test environment validation with missing .env file"""
        # Create an instance without calling the constructor
        instance = GitHubContributionHack()
        
        # Mock os.path.exists to return False for .env
        with patch('os.path.exists', return_value=False):
            # Should raise EnvironmentError when called directly
            with self.assertRaises(EnvironmentError):
                # Call the actual implementation, not the mock
                GitHubContributionHack._validate_environment(instance)

if __name__ == "__main__":
    unittest.main() 