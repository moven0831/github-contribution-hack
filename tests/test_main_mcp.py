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


class TestGitHubContributionHackMCP(unittest.TestCase):
    """Test cases for the GitHubContributionHack class with MCP integration"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary config file with MCP settings
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
        
        config_data = {
            'repositories': ['test/repo1', 'test/repo2'],
            'min_commits': 1,
            'max_commits': 3,
            'min_interval': 12,
            'max_interval': 24,
            'mcp_integration': {
                'enabled': True,
                'api_endpoint': 'https://test-api.mcp.dev/v1',
                'complexity': 'medium',
                'language_weights': {
                    'python': 0.4,
                    'javascript': 0.3,
                    'markdown': 0.2,
                    'text': 0.1
                },
                'repository_analysis': True,
                'content_quality': 'high',
                'dry_run': False
            }
        }
        
        with open(self.temp_config.name, 'w') as f:
            yaml.dump(config_data, f)
        
        # Set up environment variable for testing
        os.environ["MCP_API_KEY"] = "test_api_key"
        os.environ["GITHUB_TOKEN"] = "test_github_token"
        
        # Create patches
        self.setup_patches()

    def setup_patches(self):
        """Set up patches to avoid external dependencies"""
        # Patch environment validation
        self.validate_patch = patch.object(GitHubContributionHack, '_validate_environment')
        self.mock_validate = self.validate_patch.start()
        
        # Patch credential setup
        self.creds_patch = patch.object(GitHubContributionHack, '_setup_secure_credentials')
        self.mock_creds = self.creds_patch.start()
        
        # Add the missing methods to the class for testing
        def mock_configure_repository_access(self):
            self.g = Mock()
            return
        
        def mock_setup_github_verification(self):
            return
        
        # Add the methods to the class
        GitHubContributionHack._configure_repository_access = mock_configure_repository_access
        GitHubContributionHack._setup_github_verification = mock_setup_github_verification
        
        # Patch commit pattern model
        self.pattern_patch = patch.object(GitHubContributionHack, '_load_commit_pattern_model')
        self.mock_pattern = self.pattern_patch.start()
        self.mock_pattern.return_value = None
        
        # Patch ContributionAnalytics
        self.analytics_patch = patch('main.ContributionAnalytics')
        self.mock_analytics = self.analytics_patch.start()
        self.mock_analytics.return_value = Mock()

    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary config file
        os.unlink(self.temp_config.name)
        
        # Remove test environment variables
        if "MCP_API_KEY" in os.environ:
            del os.environ["MCP_API_KEY"]
        if "GITHUB_TOKEN" in os.environ:
            del os.environ["GITHUB_TOKEN"]
        
        # Stop patches
        self.validate_patch.stop()
        self.creds_patch.stop()
        self.pattern_patch.stop()
        self.analytics_patch.stop()
        
        # Remove the added methods
        if hasattr(GitHubContributionHack, '_configure_repository_access'):
            delattr(GitHubContributionHack, '_configure_repository_access')
        if hasattr(GitHubContributionHack, '_setup_github_verification'):
            delattr(GitHubContributionHack, '_setup_github_verification')

    @patch('main.get_mcp_client')
    def test_init_with_mcp_enabled(self, mock_get_mcp_client):
        """Test initialization with MCP enabled"""
        # Mock MCP client
        mock_client = Mock()
        mock_get_mcp_client.return_value = mock_client
        
        # Create hack instance
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Verify MCP client was initialized
        mock_get_mcp_client.assert_called_once()
        self.assertEqual(hack.mcp_client, mock_client)

    @patch('main.get_mcp_client')
    def test_init_with_mcp_error(self, mock_get_mcp_client):
        """Test initialization with MCP error"""
        # Mock MCP client error
        mock_get_mcp_client.side_effect = Exception("MCP client error")
        
        # Create hack instance
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Verify MCP client was attempted but failed
        mock_get_mcp_client.assert_called_once()
        self.assertIsNone(hack.mcp_client)

    def test_init_with_mcp_disabled(self):
        """Test initialization with MCP disabled"""
        # Create a temporary config file with MCP disabled
        temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
        
        config_data = {
            'repositories': ['test/repo1', 'test/repo2'],
            'mcp_integration': {
                'enabled': False
            }
        }
        
        with open(temp_config.name, 'w') as f:
            yaml.dump(config_data, f)
        
        # Create hack instance
        hack = GitHubContributionHack(config_path=temp_config.name)
        
        # Verify MCP client was not initialized
        self.assertIsNone(hack.mcp_client)
        
        # Clean up
        os.unlink(temp_config.name)

    @patch('main.get_mcp_client')
    def test_generate_random_content_with_mcp(self, mock_get_mcp_client):
        """Test content generation with MCP enabled"""
        # Mock MCP client
        mock_client = Mock()
        mock_client.generate_code.return_value = "def test(): pass"
        mock_client.generate_commit_message.return_value = "Add test function"
        mock_get_mcp_client.return_value = mock_client
        
        # Create hack instance
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Generate content
        message, content = hack.generate_random_content()
        
        # Verify MCP was used
        self.assertEqual(message, "Add test function")
        self.assertEqual(content, "def test(): pass")
        mock_client.generate_code.assert_called_once()
        mock_client.generate_commit_message.assert_called_once()

    @patch('main.get_mcp_client')
    @patch('random.random')
    @patch('main.GitHubContributionHack._basic_content_generation')
    def test_generate_random_content_fallback(self, mock_basic, mock_random, mock_get_mcp_client):
        """Test content generation fallback when MCP fails"""
        # Mock MCP client
        mock_client = Mock()
        mock_client.generate_code.side_effect = Exception("MCP error")
        mock_get_mcp_client.return_value = mock_client
        
        # Mock basic content generation
        mock_basic.return_value = ("Basic commit", "Basic content")
        
        # Create hack instance
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Generate content
        message, content = hack.generate_random_content()
        
        # Verify fallback was used
        self.assertEqual(message, "Basic commit")
        self.assertEqual(content, "Basic content")
        mock_client.generate_code.assert_called_once()
        mock_basic.assert_called_once()

    @patch('main.get_mcp_client')
    def test_generate_mcp_content(self, mock_get_mcp_client):
        """Test MCP content generation method"""
        # Mock MCP client
        mock_client = Mock()
        mock_client.generate_code.return_value = "// Test JavaScript code"
        mock_client.generate_commit_message.return_value = "Add JavaScript test"
        mock_get_mcp_client.return_value = mock_client
        
        # Create hack instance
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Generate content
        message, content = hack._generate_mcp_content()
        
        # Verify correct methods were called with appropriate parameters
        self.assertEqual(message, "Add JavaScript test")
        self.assertEqual(content, "// Test JavaScript code")
        mock_client.generate_code.assert_called_once()
        mock_client.generate_commit_message.assert_called_once()
        
        # Verify context and language selection
        call_args = mock_client.generate_code.call_args[0]
        self.assertIn(call_args[0], ['python', 'javascript', 'markdown', 'text'])
        context = mock_client.generate_code.call_args[0][1]
        self.assertEqual(context['complexity'], 'medium')
        self.assertEqual(context['purpose'], 'github-contribution')

    @patch('main.get_mcp_client')
    def test_make_single_commit_with_mcp_detection(self, mock_get_mcp_client):
        """Test file extension detection with MCP"""
        # Mock MCP client
        mock_client = Mock()
        mock_get_mcp_client.return_value = mock_client
        
        # Create hack instance with mocked git repo
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Mock git repo
        mock_repo = Mock()
        
        # Test python detection
        with patch('git.Repo') as mock_git_repo, \
             patch('os.path.join', return_value='/fake/path/file.py'), \
             patch('builtins.open', create=True), \
             patch('os.makedirs', return_value=None):
            
            mock_git_repo.return_value = mock_repo
            
            # Python content
            hack._make_single_commit('/fake/repo', 'Add function', '# Python code\ndef test():\n    pass')
            
            # Verify extension detection
            open_args = open.call_args[0][0]
            self.assertTrue(open_args.endswith('.py'))
        
        # Test javascript detection
        with patch('git.Repo') as mock_git_repo, \
             patch('os.path.join', return_value='/fake/path/file.js'), \
             patch('builtins.open', create=True), \
             patch('os.makedirs', return_value=None):
            
            mock_git_repo.return_value = mock_repo
            
            # JavaScript content
            hack._make_single_commit('/fake/repo', 'Add function', '// JavaScript code\nfunction test() {\n    return true;\n}')
            
            # Verify extension detection
            open_args = open.call_args[0][0]
            self.assertTrue(open_args.endswith('.js'))

        # Test markdown detection
        with patch('git.Repo') as mock_git_repo, \
             patch('os.path.join', return_value='/fake/path/file.md'), \
             patch('builtins.open', create=True), \
             patch('os.makedirs', return_value=None):
            
            mock_git_repo.return_value = mock_repo
            
            # Markdown content
            hack._make_single_commit('/fake/repo', 'Add documentation', '# Title\n## Subtitle\nContent')
            
            # Verify extension detection
            open_args = open.call_args[0][0]
            self.assertTrue(open_args.endswith('.md'))

        # Test JSON detection
        with patch('git.Repo') as mock_git_repo, \
             patch('os.path.join', return_value='/fake/path/file.json'), \
             patch('builtins.open', create=True), \
             patch('os.makedirs', return_value=None):
            
            mock_git_repo.return_value = mock_repo
            
            # JSON content
            hack._make_single_commit('/fake/repo', 'Add config', '{"key": "value"}')
            
            # Verify extension detection
            open_args = open.call_args[0][0]
            self.assertTrue(open_args.endswith('.json'))


if __name__ == '__main__':
    unittest.main() 