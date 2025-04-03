"""
Extended unit tests for MCP integration functionality
These tests cover additional aspects of MCP integration not covered in the main test file.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, Mock
import tempfile
import json
import pytest
from datetime import datetime

# Add parent directory to path so we can import modules
sys.path.insert(0, '.')

# Import the modules to test
from mcp_integration import MCPClient, get_mcp_client
from main import GitHubContributionHack
from retry import retry_with_backoff

class TestMCPContentGeneration(unittest.TestCase):
    """Tests for MCP content generation capabilities"""
    
    def setUp(self):
        """Set up test environment"""
        # Set up environment variable for testing
        os.environ["MCP_API_KEY"] = "test_api_key"
        os.environ["MCP_API_ENDPOINT"] = "https://test-api.mcp.dev/v1"
        
        # Create the client instance
        self.client = MCPClient()

    def tearDown(self):
        """Clean up after tests"""
        # Remove test environment variables
        if "MCP_API_KEY" in os.environ:
            del os.environ["MCP_API_KEY"]
        if "MCP_API_ENDPOINT" in os.environ:
            del os.environ["MCP_API_ENDPOINT"]

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_html_content(self, mock_api_request):
        """Test HTML content generation"""
        # Mock successful API response
        mock_api_request.return_value = {"code": "<div class='test'>Hello World</div>"}
        
        # Call the method
        result = self.client.generate_code("html")
        
        # Verify the result
        self.assertEqual(result, "<div class='test'>Hello World</div>")
        
        # Verify API call parameters
        mock_api_request.assert_called_once()
        args = mock_api_request.call_args[0]
        kwargs = mock_api_request.call_args[1]
        self.assertEqual(args[0], "generate/code")
        self.assertEqual(kwargs["task"], "code_generation")
        self.assertEqual(kwargs["language"], "html")

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_json_content(self, mock_api_request):
        """Test JSON content generation"""
        # Mock successful API response
        mock_api_request.return_value = {"code": '{"name": "test", "value": 123}'}
        
        # Call the method
        result = self.client.generate_code("json")
        
        # Verify the result
        self.assertEqual(result, '{"name": "test", "value": 123}')
        
        # Verify API call parameters
        mock_api_request.assert_called_once()
        args = mock_api_request.call_args[0]
        kwargs = mock_api_request.call_args[1]
        self.assertEqual(args[0], "generate/code")
        self.assertEqual(kwargs["task"], "code_generation")
        self.assertEqual(kwargs["language"], "json")

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_complex_context(self, mock_api_request):
        """Test code generation with complex context"""
        # Mock successful API response
        mock_api_request.return_value = {"code": "def complex_func(): pass"}
        
        # Create complex context
        complex_context = {
            "purpose": "testing",
            "complexity": "high",
            "required_imports": ["os", "sys", "datetime"],
            "function_name": "complex_func",
            "parameters": ["param1", "param2"],
            "return_type": "dict",
            "dependencies": {
                "external": ["numpy", "pandas"],
                "internal": ["utils", "helpers"]
            }
        }
        
        # Call the method
        result = self.client.generate_code("python", complex_context)
        
        # Verify the result
        self.assertEqual(result, "def complex_func(): pass")
        
        # Verify API call parameters
        mock_api_request.assert_called_once()
        args = mock_api_request.call_args[0]
        kwargs = mock_api_request.call_args[1]
        self.assertEqual(args[0], "generate/code")
        self.assertEqual(kwargs["task"], "code_generation")
        self.assertEqual(kwargs["language"], "python")
        self.assertEqual(kwargs["context"], complex_context)

    def test_generate_fallback_code_unknown_language(self):
        """Test fallback code generation for unknown language"""
        # Call with unknown language
        code = self.client._generate_fallback_code("unknown_language")
        
        # Verify generic fallback was generated
        self.assertIn("Generated fallback content", code)
        self.assertIn("This is a placeholder", code)

class TestMCPClientRetryLogic(unittest.TestCase):
    """Tests for the retry logic in MCP client"""
    
    def setUp(self):
        """Set up test environment"""
        os.environ["MCP_API_KEY"] = "test_api_key"
        os.environ["MCP_API_ENDPOINT"] = "https://test-api.mcp.dev/v1"
        self.client = MCPClient()

    def tearDown(self):
        """Clean up after tests"""
        if "MCP_API_KEY" in os.environ:
            del os.environ["MCP_API_KEY"]
        if "MCP_API_ENDPOINT" in os.environ:
            del os.environ["MCP_API_ENDPOINT"]

    @patch('mcp_integration.requests.post')
    def test_retry_on_connection_error(self, mock_post):
        """Test that connection errors trigger retry logic"""
        # Setup mock to fail with connection error twice, then succeed
        mock_post.side_effect = [
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed again"),
            MagicMock(status_code=200, json=lambda: {"code": "test_code"})
        ]
        
        # Test the real retry logic
        # We'll use a shorter backoff for testing
        original_retry = mcp_integration.retry_with_backoff
        try:
            # Patch retry decorator to use shorter times
            mcp_integration.retry_with_backoff = lambda max_retries=3, backoff_factor=0.1: original_retry(
                max_retries=max_retries, backoff_factor=backoff_factor
            )
            
            # Call API method that should retry
            result = self.client._make_api_request("test/endpoint", {"param": "value"})
            
            # Verify the result after retries
            self.assertEqual(result, {"code": "test_code"})
            
            # Verify post was called 3 times (2 failures + 1 success)
            self.assertEqual(mock_post.call_count, 3)
        finally:
            # Restore original retry decorator
            mcp_integration.retry_with_backoff = original_retry

    @patch('mcp_integration.requests.post')
    def test_retry_on_timeout(self, mock_post):
        """Test that timeouts trigger retry logic"""
        # Setup mock to fail with timeout twice, then succeed
        mock_post.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out again"),
            MagicMock(status_code=200, json=lambda: {"code": "test_code"})
        ]
        
        # Test the real retry logic with shorter backoff
        original_retry = mcp_integration.retry_with_backoff
        try:
            # Patch retry decorator to use shorter times
            mcp_integration.retry_with_backoff = lambda max_retries=3, backoff_factor=0.1: original_retry(
                max_retries=max_retries, backoff_factor=backoff_factor
            )
            
            # Call API method that should retry
            result = self.client._make_api_request("test/endpoint", {"param": "value"})
            
            # Verify the result after retries
            self.assertEqual(result, {"code": "test_code"})
            
            # Verify post was called 3 times
            self.assertEqual(mock_post.call_count, 3)
        finally:
            # Restore original retry decorator
            mcp_integration.retry_with_backoff = original_retry

    @patch('mcp_integration.requests.post')
    def test_max_retries_exceeded(self, mock_post):
        """Test behavior when max retries is exceeded"""
        # Setup mock to always fail
        mock_post.side_effect = ConnectionError("Connection failed")
        
        # Test the real retry logic with shorter backoff
        original_retry = mcp_integration.retry_with_backoff
        try:
            # Patch retry decorator to use shorter times and fewer retries
            mcp_integration.retry_with_backoff = lambda max_retries=2, backoff_factor=0.1: original_retry(
                max_retries=max_retries, backoff_factor=backoff_factor
            )
            
            # Call API method that should retry and ultimately fail
            result = self.client._make_api_request("test/endpoint", {"param": "value"})
            
            # Verify the result is None after max retries
            self.assertIsNone(result)
            
            # Verify post was called the expected number of times (max_retries + 1)
            self.assertEqual(mock_post.call_count, 3)
        finally:
            # Restore original retry decorator
            mcp_integration.retry_with_backoff = original_retry

class TestMCPIntegrationInMain(unittest.TestCase):
    """Test MCP integration in the main GitHubContributionHack class"""
    
    def setUp(self):
        """Set up test environment"""
        # Set up environment variable for testing
        self.original_environ = os.environ.copy()
        os.environ["GITHUB_TOKEN"] = "test_token"
        os.environ["MCP_API_KEY"] = "test_api_key"
        
        # Create a temporary config file with MCP enabled
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
        with open(self.temp_config.name, 'w') as f:
            f.write("""
            repositories:
              - test/repo1
            min_commits: 1
            max_commits: 3
            mcp_integration:
              enabled: true
              complexity: "medium"
              language_weights:
                python: 0.5
                javascript: 0.3
                markdown: 0.2
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
    @patch('main.GitHubContributionHack._setup_secure_credentials')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    @patch('main.ContributionAnalytics')
    @patch('main.get_mcp_client')
    def test_mcp_initialization_enabled(self, mock_get_client, mock_analytics, mock_pattern, 
                                       mock_verification, mock_repo_access, mock_credentials, 
                                       mock_validate):
        """Test MCP initialization when enabled"""
        # Setup mock
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Create instance
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Verify MCP client was initialized
        mock_get_client.assert_called_once()
        self.assertEqual(hack.mcp_client, mock_client)
        
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._setup_secure_credentials')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    @patch('main.ContributionAnalytics')
    @patch('main.get_mcp_client')
    def test_mcp_initialization_enabled_but_fails(self, mock_get_client, mock_analytics, mock_pattern, 
                                                mock_verification, mock_repo_access, mock_credentials, 
                                                mock_validate):
        """Test MCP initialization when enabled but fails"""
        # Setup mock to raise exception
        mock_get_client.side_effect = Exception("MCP initialization failed")
        
        # Create instance (should not raise exception)
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Verify MCP client was attempted but not set
        mock_get_client.assert_called_once()
        self.assertIsNone(hack.mcp_client)
    
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._setup_secure_credentials')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    @patch('main.ContributionAnalytics')
    def test_mcp_initialization_disabled(self, mock_analytics, mock_pattern, 
                                        mock_verification, mock_repo_access, mock_credentials, 
                                        mock_validate):
        """Test MCP initialization when disabled"""
        # Create a temporary config file with MCP disabled
        temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
        try:
            with open(temp_config.name, 'w') as f:
                f.write("""
                repositories:
                  - test/repo1
                min_commits: 1
                max_commits: 3
                mcp_integration:
                  enabled: false
                """)
            
            # Create instance
            hack = GitHubContributionHack(config_path=temp_config.name)
            
            # Verify MCP client was not initialized
            self.assertIsNone(hack.mcp_client)
            
        finally:
            # Clean up
            if os.path.exists(temp_config.name):
                os.unlink(temp_config.name)
    
    @patch('main.GitHubContributionHack._validate_environment')
    @patch('main.GitHubContributionHack._setup_secure_credentials')
    @patch('main.GitHubContributionHack._configure_repository_access')
    @patch('main.GitHubContributionHack._setup_github_verification')
    @patch('main.GitHubContributionHack._load_commit_pattern_model')
    @patch('main.ContributionAnalytics')
    @patch('main.get_mcp_client')
    def test_generate_random_content_with_mcp(self, mock_get_client, mock_analytics, mock_pattern, 
                                             mock_verification, mock_repo_access, mock_credentials, 
                                             mock_validate):
        """Test content generation with MCP"""
        # Setup mock
        mock_client = Mock()
        mock_client.generate_code.return_value = "def test_function(): return 'MCP generated code'"
        mock_client.generate_commit_message.return_value = "MCP generated commit message"
        mock_get_client.return_value = mock_client
        
        # Create instance
        hack = GitHubContributionHack(config_path=self.temp_config.name)
        
        # Call the method
        message, content = hack.generate_random_content()
        
        # Verify MCP was used for generation
        self.assertEqual(message, "MCP generated commit message")
        self.assertEqual(content, "def test_function(): return 'MCP generated code'")
        mock_client.generate_commit_message.assert_called_once()
        mock_client.generate_code.assert_called_once()

if __name__ == "__main__":
    unittest.main() 