"""
Unit tests for MCP integration in the main GitHub Contribution Hack script
"""
import os
import unittest
from unittest.mock import patch, MagicMock, Mock
import yaml
import tempfile
from datetime import datetime
import json

# Import the modules to test
from main import GitHubContributionHack
from config_loader import ConfigManager # Import ConfigManager for type hinting if needed


class TestGitHubContributionHackMCP(unittest.TestCase):
    """Test cases for the GitHubContributionHack class with MCP integration"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary config file with MCP settings
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml')
        
        self.config_data = {
            'repositories': ['test/repo1', 'test/repo2'],
            'min_commits': 1,
            'max_commits': 3,
            'min_interval': 12,
            'max_interval': 24,
            'database': {'path': 'test_contributions.db'}, # Added for ConfigManager
            'performance': { # Added for ConfigManager
                'max_workers': 2,
                'parallel_repos': False
            },
            'commit_generation': { # Added for ConfigManager
                'ml_based_chance': 0.5,
                'code_content_chance': 0.5,
                'file_types': ['py', 'txt']
            },
            'mcp_integration': {
                'enabled': True,
                # api_key is intentionally omitted here to test fallback to env var
                'api_endpoint': 'https://test-api.mcp.dev/v1/config', # Distinct from potential env var
                'complexity': 'medium',
                'max_retries': 5, # Configured value
                'request_timeout': 25, # Configured value
                'language_weights': {
                    'python': 0.4,
                    'javascript': 0.3,
                    'markdown': 0.2,
                    'text': 0.1
                },
                'repository_analysis': True,
                'content_quality': 'high',
                'dry_run': False
            },
            'notifications': { 'enabled': False } # Added for ConfigManager
        }
        
        yaml.dump(self.config_data, self.temp_config_file)
        self.temp_config_file.close() # Close the file before GitHubContributionHack tries to read it
        self.temp_config_path = self.temp_config_file.name
        
        # Set up environment variables for testing fallbacks and required ones
        os.environ["MCP_API_KEY"] = "test_mcp_api_key_env" # Crucial for MCPClient if not in config
        os.environ["GITHUB_TOKEN"] = "test_github_token_env" # For _setup_secure_credentials if not fully mocked
        
        # Create patches
        self.setup_patches()

    def setup_patches(self):
        """Set up patches to avoid external dependencies"""
        self.validate_patch = patch.object(GitHubContributionHack, '_validate_environment', return_value=None)
        self.mock_validate = self.validate_patch.start()
        self.addCleanup(self.validate_patch.stop)
        
        self.creds_patch = patch.object(GitHubContributionHack, '_setup_secure_credentials', return_value=None)
        self.mock_creds = self.creds_patch.start()
        self.addCleanup(self.creds_patch.stop)
        
        self.github_verify_patch = patch.object(GitHubContributionHack, '_setup_github_verification', return_value=None)
        self.mock_github_verify = self.github_verify_patch.start()
        self.addCleanup(self.github_verify_patch.stop)
        
        self.pattern_patch = patch.object(GitHubContributionHack, '_load_commit_pattern_model', return_value=None)
        self.mock_pattern = self.pattern_patch.start()
        self.addCleanup(self.pattern_patch.stop)
        
        self.analytics_patch = patch('main.ContributionAnalytics', return_value=MagicMock())
        self.mock_analytics_class = self.analytics_patch.start()
        self.addCleanup(self.analytics_patch.stop)

        self.notification_patch = patch('main.setup_notifications', return_value=None) # Assume notifications off for these tests
        self.mock_setup_notifications = self.notification_patch.start()
        self.addCleanup(self.notification_patch.stop)

    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.temp_config_path):
             os.unlink(self.temp_config_path)
        
        env_vars_to_clear = ["MCP_API_KEY", "GITHUB_TOKEN", "MCP_API_ENDPOINT", "MCP_MAX_RETRIES", "MCP_REQUEST_TIMEOUT"]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    @patch('main.get_mcp_client')
    def test_init_with_mcp_enabled_uses_config_manager(self, mock_get_mcp_client):
        """Test GitHubContributionHack init with MCP enabled, verifying ConfigManager is passed to get_mcp_client."""
        mock_mcp_instance = MagicMock(spec=MCPClient)
        mock_get_mcp_client.return_value = mock_mcp_instance
        
        hack = GitHubContributionHack(config_path=self.temp_config_path)
        
        self.assertTrue(hack.config_manager.get('mcp_integration.enabled'))
        mock_get_mcp_client.assert_called_once_with(hack.config_manager)
        self.assertEqual(hack.mcp_client, mock_mcp_instance)
        # Verify that setup_notifications was also called with the config_manager
        self.mock_setup_notifications.assert_called_once_with(hack.config_manager)

    @patch('main.get_mcp_client')
    def test_init_with_mcp_initialization_error(self, mock_get_mcp_client):
        """Test GitHubContributionHack init when get_mcp_client returns None (e.g., API key missing)."""
        mock_get_mcp_client.return_value = None # Simulate MCP client failing to init
        
        hack = GitHubContributionHack(config_path=self.temp_config_path)
        
        self.assertTrue(hack.config_manager.get('mcp_integration.enabled')) # MCP is configured as enabled
        mock_get_mcp_client.assert_called_once_with(hack.config_manager)
        self.assertIsNone(hack.mcp_client) # But the instance should be None due to init failure

    def test_init_with_mcp_disabled_in_config(self):
        """Test GitHubContributionHack init when MCP is disabled in the config file."""
        disabled_config_data = self.config_data.copy()
        disabled_config_data['mcp_integration']['enabled'] = False
        
        temp_disabled_config_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml')
        yaml.dump(disabled_config_data, temp_disabled_config_file)
        temp_disabled_config_file.close()

        with patch('main.get_mcp_client') as mock_get_mcp_client_disabled:
            hack = GitHubContributionHack(config_path=temp_disabled_config_file.name)
            self.assertFalse(hack.config_manager.get('mcp_integration.enabled'))
            mock_get_mcp_client_disabled.assert_not_called() # Should not even attempt to get client
            self.assertIsNone(hack.mcp_client)
        
        os.unlink(temp_disabled_config_file.name)

    @patch('main.GitHubContributionHack._generate_mcp_content')
    @patch('main.GitHubContributionHack._basic_content_generation')
    def test_generate_random_content_mcp_enabled_and_client_exists(self, mock_basic_gen, mock_mcp_gen):
        """ Test generate_random_content uses MCP if enabled and client exists."""
        mock_mcp_gen.return_value = ("mcp_msg", "mcp_content")
        hack = GitHubContributionHack(config_path=self.temp_config_path)
        hack.mcp_client = MagicMock() # Ensure client exists
        
        # Ensure mcp_integration.enabled is True from config
        self.assertTrue(hack.config_manager.get('mcp_integration.enabled'))

        msg, content = hack.generate_random_content()
        
        mock_mcp_gen.assert_called_once()
        mock_basic_gen.assert_not_called()
        self.assertEqual(msg, "mcp_msg")
        self.assertEqual(content, "mcp_content")

    @patch('main.GitHubContributionHack._generate_mcp_content') # Mock this to prevent its actual execution
    @patch('random.random') # Used for non-MCP path
    @patch('main.GitHubContributionHack._basic_content_generation') # Used for non-MCP path
    def test_generate_random_content_mcp_enabled_but_no_client(self, mock_basic_gen, mock_random, mock_mcp_gen_method):
        """Test generate_random_content falls back if MCP enabled but client is None."""
        mock_basic_gen.return_value = ("basic_msg", "basic_content")
        mock_random.return_value = 0.8 # Ensure it goes to basic_content_generation path
        
        hack = GitHubContributionHack(config_path=self.temp_config_path)
        hack.mcp_client = None # Simulate client failing to initialize
        self.assertTrue(hack.config_manager.get('mcp_integration.enabled')) # MCP is configured as enabled

        msg, content = hack.generate_random_content()

        mock_mcp_gen_method.assert_not_called() # _generate_mcp_content itself should not be called
        mock_basic_gen.assert_called_once()
        self.assertEqual(msg, "basic_msg")
        self.assertEqual(content, "basic_content")

    # Test the _generate_mcp_content method directly
    @patch('main.get_mcp_client') # This is called during __init__
    def test_internal_generate_mcp_content_success(self, mock_get_mcp_client_for_init):
        """Test _generate_mcp_content successfully calls mcp_client methods."""
        hack = GitHubContributionHack(config_path=self.temp_config_path)
        
        # Ensure mcp_client is set up on the hack instance for this test
        mock_mcp_client_instance = MagicMock(spec=MCPClient)
        mock_mcp_client_instance.generate_code.return_value = "// Test JS from MCP"
        mock_mcp_client_instance.generate_commit_message.return_value = "JS commit from MCP"
        hack.mcp_client = mock_mcp_client_instance
        
        # Verify mcp_integration.enabled from config
        self.assertTrue(hack.config_manager.get('mcp_integration.enabled'))
        # Verify language weights and complexity are read from config
        expected_lang_weights = self.config_data['mcp_integration']['language_weights']
        expected_complexity = self.config_data['mcp_integration']['complexity']

        self.assertEqual(hack.config_manager.get('mcp_integration.language_weights'), expected_lang_weights)
        self.assertEqual(hack.config_manager.get('mcp_integration.complexity'), expected_complexity)

        message, content = hack._generate_mcp_content()
        
        self.assertEqual(message, "JS commit from MCP")
        self.assertEqual(content, "// Test JS from MCP")
        
        mock_mcp_client_instance.generate_code.assert_called_once()
        call_args_code = mock_mcp_client_instance.generate_code.call_args[0]
        self.assertIn(call_args_code[0], expected_lang_weights.keys()) # Language
        self.assertEqual(call_args_code[1]['complexity'], expected_complexity) # Context
        self.assertEqual(call_args_code[1]['purpose'], 'github-contribution')

        mock_mcp_client_instance.generate_commit_message.assert_called_once()
        # Could add more assertions on generate_commit_message args if needed

    @patch('main.get_mcp_client') # For __init__
    def test_internal_generate_mcp_content_client_failure_falls_back(self, mock_get_mcp_client_for_init):
        """Test _generate_mcp_content falls back to basic if mcp_client calls fail."""
        hack = GitHubContributionHack(config_path=self.temp_config_path)

        mock_mcp_client_instance = MagicMock(spec=MCPClient)
        mock_mcp_client_instance.generate_code.side_effect = Exception("MCP API dead")
        hack.mcp_client = mock_mcp_client_instance
        
        # Mock the _basic_content_generation method for this specific test
        with patch.object(hack, '_basic_content_generation', return_value=("fallback_msg", "fallback_content")) as mock_basic:
            message, content = hack._generate_mcp_content()
            self.assertEqual(message, "fallback_msg")
            self.assertEqual(content, "fallback_content")
            mock_basic.assert_called_once()

    # Test _make_single_commit file extension detection
    # This test is a bit complex due to nested mocks. Consider simplifying if it becomes brittle.
    @patch('main.git.Repo') # Mock the git.Repo call
    @patch('builtins.open') # Mock file open
    @patch('main.get_mcp_client') # For __init__
    def test_make_single_commit_mcp_file_type_detection(self, mock_get_mcp_client_init, mock_open, mock_git_repo_class):
        """Test that _make_single_commit uses config for MCP file type detection logic."""
        hack = GitHubContributionHack(config_path=self.temp_config_path)
        hack.mcp_client = MagicMock() # Ensure client exists for the mcp_integration.enabled check
        self.assertTrue(hack.config_manager.get('mcp_integration.enabled'))

        mock_repo_instance = MagicMock()
        mock_git_repo_class.return_value = mock_repo_instance

        # Python content
        py_content = "# Python code\ndef hello():\n  print('hello')"
        hack._make_single_commit("dummy/path", "py commit", py_content)
        args_list_py = mock_open.call_args_list
        # The file path for writing content should end with .py
        write_call_path_py = args_list_py[-1][0][0] # Path is the first arg of the last call to open
        self.assertTrue(write_call_path_py.endswith('.py'))

        # JS content
        js_content = "// JS code\nfunction world() { console.log('world'); }"
        hack._make_single_commit("dummy/path", "js commit", js_content)
        args_list_js = mock_open.call_args_list
        write_call_path_js = args_list_js[-1][0][0]
        self.assertTrue(write_call_path_js.endswith('.js'))

        # Markdown content
        md_content = "# Markdown\n## Section"
        hack._make_single_commit("dummy/path", "md commit", md_content)
        args_list_md = mock_open.call_args_list
        write_call_path_md = args_list_md[-1][0][0]
        self.assertTrue(write_call_path_md.endswith('.md'))

        # JSON content
        json_content = "{\"key\": \"value\"}"
        hack._make_single_commit("dummy/path", "json commit", json_content)
        args_list_json = mock_open.call_args_list
        write_call_path_json = args_list_json[-1][0][0]
        self.assertTrue(write_call_path_json.endswith('.json'))

        # Text content (fallback)
        txt_content = "Plain text content"
        hack._make_single_commit("dummy/path", "txt commit", txt_content)
        args_list_txt = mock_open.call_args_list
        write_call_path_txt = args_list_txt[-1][0][0]
        self.assertTrue(write_call_path_txt.endswith('.txt'))

if __name__ == '__main__':
    unittest.main() 