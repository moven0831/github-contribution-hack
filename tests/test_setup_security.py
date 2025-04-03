"""
Unit tests for setup_security.py
"""
import unittest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import datetime
import pytest

# Add parent directory to path so we can import modules
sys.path.insert(0, '.')

# Import the module to test
from setup_security import SecuritySetup

class TestSecuritySetup(unittest.TestCase):
    """Test case for SecuritySetup class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Save original values to restore later
        self.original_env_file = SecuritySetup.ENV_FILE
        self.original_key_storage = SecuritySetup.KEY_STORAGE_FILE
        
        # Set paths to use temporary directory
        SecuritySetup.ENV_FILE = os.path.join(self.temp_dir.name, '.env')
        SecuritySetup.KEY_STORAGE_FILE = os.path.join(self.temp_dir.name, '.key_info')
        
        # Setup environment for tests
        self.original_environ = os.environ.copy()
        os.environ["GITHUB_TOKEN"] = "test_token"
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original values
        SecuritySetup.ENV_FILE = self.original_env_file
        SecuritySetup.KEY_STORAGE_FILE = self.original_key_storage
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_environ)
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('setup_security.dotenv')
    def test_init(self, mock_dotenv):
        """Test initialization of SecuritySetup"""
        setup = SecuritySetup()
        
        # Should have called load_dotenv
        mock_dotenv.load_dotenv.assert_called_once()
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', False)
    @patch('setup_security.SecuritySetup.install_dependencies')
    def test_check_dependencies_missing(self, mock_install):
        """Test dependency checking when dependencies are missing"""
        setup = SecuritySetup()
        
        # Should have called install_dependencies
        mock_install.assert_called_once()
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    def test_update_env_file_new(self):
        """Test updating a new .env file"""
        # Ensure .env doesn't exist yet
        if os.path.exists(SecuritySetup.ENV_FILE):
            os.unlink(SecuritySetup.ENV_FILE)
        
        # Create instance and update env file
        setup = SecuritySetup()
        setup.update_env_file("new_test_token")
        
        # Check that file was created with correct content
        self.assertTrue(os.path.exists(SecuritySetup.ENV_FILE))
        
        with open(SecuritySetup.ENV_FILE, 'r') as f:
            content = f.read()
            self.assertIn("GITHUB_TOKEN=new_test_token", content)
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    def test_update_env_file_existing(self):
        """Test updating an existing .env file"""
        # Create .env file with existing token
        with open(SecuritySetup.ENV_FILE, 'w') as f:
            f.write("GITHUB_TOKEN=old_token\nOTHER_VAR=value\n")
        
        # Create instance and update env file
        setup = SecuritySetup()
        setup.update_env_file("updated_token")
        
        # Check that file was updated correctly
        with open(SecuritySetup.ENV_FILE, 'r') as f:
            content = f.read()
            self.assertIn("GITHUB_TOKEN=updated_token", content)
            self.assertIn("OTHER_VAR=value", content)
            self.assertNotIn("old_token", content)
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    def test_replace_env_var(self):
        """Test replacing environment variables in content"""
        setup = SecuritySetup()
        
        content = "VAR1=old1\nVAR2=keep2\nVAR3=old3"
        
        # Replace VAR1
        result = setup.replace_env_var(content, "VAR1", "new1")
        self.assertEqual(result, "VAR1=new1\nVAR2=keep2\nVAR3=old3")
        
        # Replace VAR3
        result = setup.replace_env_var(content, "VAR3", "new3")
        self.assertEqual(result, "VAR1=old1\nVAR2=keep2\nVAR3=new3")
        
        # Replace non-existent variable
        result = setup.replace_env_var(content, "VAR4", "new4")
        self.assertEqual(result, "VAR1=old1\nVAR2=keep2\nVAR3=old3")
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('setup_security.keyring')
    @patch('setup_security.Fernet')
    def test_setup_keyring(self, mock_fernet, mock_keyring):
        """Test keyring setup"""
        # Setup mocks
        mock_cipher = MagicMock()
        mock_cipher.encrypt.return_value = b'encrypted_data'
        mock_fernet.generate_key.return_value = b'test_key'
        mock_fernet.return_value = mock_cipher
        
        # Create instance with mocked save_key_info
        setup = SecuritySetup()
        setup.save_key_info = MagicMock()
        
        # Call method
        setup.setup_keyring("test_token")
        
        # Verify encryption and storage
        mock_fernet.generate_key.assert_called_once()
        mock_cipher.encrypt.assert_called_once_with(b'test_token')
        mock_keyring.set_password.assert_called_once_with(
            setup.KEYRING_SERVICE, setup.KEYRING_USERNAME, 'encrypted_data'
        )
        setup.save_key_info.assert_called_once_with(b'test_key')
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('setup_security.keyring')
    @patch('setup_security.Fernet')
    def test_setup_keyring_exception(self, mock_fernet, mock_keyring):
        """Test keyring setup with exception"""
        # Setup mocks
        mock_cipher = MagicMock()
        mock_fernet.generate_key.return_value = b'test_key'
        mock_fernet.return_value = mock_cipher
        mock_keyring.set_password.side_effect = Exception("Keyring error")
        
        # Create instance with mocked save_key_info
        setup = SecuritySetup()
        setup.save_key_info = MagicMock()
        
        # Call method (should not raise exception)
        setup.setup_keyring("test_token")
        
        # Should not have called save_key_info
        setup.save_key_info.assert_not_called()
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    def test_hash_key(self):
        """Test key hashing function"""
        setup = SecuritySetup()
        key = b'test_key_for_hashing'
        
        # Call method
        result = setup.hash_key(key)
        
        # Verify result is a non-empty string with expected length
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 8)
        
        # Call again to verify consistency
        result2 = setup.hash_key(key)
        self.assertEqual(result, result2)
        
        # Hash a different key to verify difference
        result3 = setup.hash_key(b'different_key')
        self.assertNotEqual(result, result3)
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('setup_security.keyring')
    def test_store_encryption_key_success(self, mock_keyring):
        """Test successful encryption key storage"""
        setup = SecuritySetup()
        setup.store_key_in_file = MagicMock()
        
        # Call method
        setup.store_encryption_key(b'test_key')
        
        # Verify keyring was used
        mock_keyring.set_password.assert_called_once_with(
            setup.KEYRING_SERVICE, 'encryption_key', 'test_key'
        )
        
        # Should not have called fallback
        setup.store_key_in_file.assert_not_called()
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('setup_security.keyring')
    def test_store_encryption_key_fallback(self, mock_keyring):
        """Test encryption key storage fallback"""
        # Setup mock to raise exception
        mock_keyring.set_password.side_effect = Exception("Keyring error")
        
        setup = SecuritySetup()
        setup.store_key_in_file = MagicMock()
        
        # Call method
        setup.store_encryption_key(b'test_key')
        
        # Should have called fallback
        setup.store_key_in_file.assert_called_once_with(b'test_key')
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.chmod')
    def test_store_key_in_file(self, mock_chmod, mock_file, mock_makedirs):
        """Test key storage in file"""
        setup = SecuritySetup()
        
        # Call method
        setup.store_key_in_file(b'test_key')
        
        # Verify directory creation
        mock_makedirs.assert_called_once()
        
        # Verify file writing
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(b'test_key')
        
        # Verify permissions setting
        mock_chmod.assert_called_once()
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('setup_security.keyring')
    def test_save_key_info(self, mock_keyring):
        """Test key info saving"""
        # Mock methods
        setup = SecuritySetup()
        setup.hash_key = MagicMock(return_value='abcd1234')
        setup.store_encryption_key = MagicMock()
        
        test_key = b'test_key'
        
        # Use mock_open to capture file writing
        m = mock_open()
        with patch('builtins.open', m):
            setup.save_key_info(test_key)
        
        # Verify hash_key was called
        setup.hash_key.assert_called_once_with(test_key)
        
        # Verify store_encryption_key was called
        setup.store_encryption_key.assert_called_once_with(test_key)
        
        # Verify file was written
        m.assert_called_once_with(setup.KEY_STORAGE_FILE, 'w')
        
        # Verify JSON content
        write_call = m().write.call_args[0][0]
        key_info = json.loads(write_call)
        self.assertEqual(key_info['key_id'], 'abcd1234')
        self.assertIn('created_at', key_info)
        self.assertIn('rotation_due', key_info)
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('builtins.input', return_value='y')
    @patch('setup_security.getpass.getpass', return_value='new_token')
    def test_prompt_for_token(self, mock_getpass, mock_input):
        """Test token prompting"""
        setup = SecuritySetup()
        result = setup.prompt_for_token()
        
        # Verify getpass was called
        mock_getpass.assert_called_once()
        
        # Verify result
        self.assertEqual(result, 'new_token')
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('setup_security.keyring')
    def test_audit_security(self, mock_keyring, mock_file, mock_exists):
        """Test security audit with no issues"""
        # Setup mocks
        mock_exists.return_value = True
        mock_keyring.get_password.return_value = 'encrypted_token'
        
        # Mock file permissions
        with patch('os.stat') as mock_stat:
            mock_stat.return_value.st_mode = 0o100600  # Regular file with 600 permissions
            
            # Mock file content for key info
            today = datetime.datetime.now()
            future = today + datetime.timedelta(days=10)
            key_info = {
                'key_id': 'abcd1234',
                'created_at': today.strftime("%Y-%m-%d %H:%M:%S"),
                'rotation_due': future.strftime("%Y-%m-%d")
            }
            mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(key_info)
            
            # Run audit
            setup = SecuritySetup()
            result = setup.audit_security()
            
            # Should return True for no issues
            self.assertTrue(result)
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('os.path.exists')
    def test_audit_security_with_issues(self, mock_exists):
        """Test security audit with issues"""
        # Setup mocks to show issues
        mock_exists.side_effect = lambda path: path == setup_security.SecuritySetup.ENV_FILE
        
        # Mock file permissions for .env
        with patch('os.stat') as mock_stat:
            mock_stat.return_value.st_mode = 0o100644  # Regular file with 644 permissions
            
            # Mock keyring error
            with patch('setup_security.keyring') as mock_keyring:
                mock_keyring.get_password.side_effect = Exception("Keyring error")
                
                # Run audit
                setup = SecuritySetup()
                result = setup.audit_security()
                
                # Should return False for issues found
                self.assertFalse(result)
    
    @patch('setup_security.DEPENDENCIES_AVAILABLE', True)
    @patch('setup_security.SecuritySetup.prompt_for_token', return_value='new_token')
    @patch('setup_security.SecuritySetup.update_env_file')
    @patch('setup_security.Fernet')
    @patch('setup_security.keyring')
    @patch('setup_security.SecuritySetup.save_key_info')
    def test_rotate_credentials(self, mock_save_key, mock_keyring, mock_fernet, 
                               mock_update_env, mock_prompt):
        """Test credential rotation"""
        # Setup mocks
        mock_cipher = MagicMock()
        mock_cipher.encrypt.return_value = b'new_encrypted_data'
        mock_fernet.generate_key.return_value = b'new_key'
        mock_fernet.return_value = mock_cipher
        
        # Call method
        setup = SecuritySetup()
        setup.rotate_credentials()
        
        # Verify methods were called
        mock_prompt.assert_called_once()
        mock_update_env.assert_called_once_with('new_token')
        mock_fernet.generate_key.assert_called_once()
        mock_cipher.encrypt.assert_called_once_with(b'new_token')
        mock_keyring.set_password.assert_called_once_with(
            setup.KEYRING_SERVICE, setup.KEYRING_USERNAME, 'new_encrypted_data'
        )
        mock_save_key.assert_called_once_with(b'new_key')

if __name__ == "__main__":
    unittest.main() 