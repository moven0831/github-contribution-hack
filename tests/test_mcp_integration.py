"""
Unit tests for MCP integration functionality
"""
import os
import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import tempfile
from datetime import datetime

# Import the modules to test
from mcp_integration import MCPClient, get_mcp_client
# Attempt to import ConfigManager, or use a mock if not found (e.g. in minimal test environments)
try:
    from config_loader import ConfigManager
except ImportError:
    ConfigManager = MagicMock()


class TestMCPClient(unittest.TestCase):
    """Test cases for the MCPClient class"""

    def setUp(self):
        """Set up test environment"""
        # Set up environment variable for testing
        os.environ["MCP_API_KEY"] = "test_api_key_env"
        os.environ["MCP_API_ENDPOINT"] = "https://test-api.mcp.dev/v1/env"
        # Reset the global mcp client instance for each test
        patcher = patch('mcp_integration._mcp_client_instance', None)
        self.addCleanup(patcher.stop)
        patcher.start()
        
        # Default client using only env vars
        self.client_env_only = MCPClient()


    def tearDown(self):
        """Clean up after tests"""
        # Remove test environment variables
        if "MCP_API_KEY" in os.environ:
            del os.environ["MCP_API_KEY"]
        if "MCP_API_ENDPOINT" in os.environ:
            del os.environ["MCP_API_ENDPOINT"]
        if "MCP_MAX_RETRIES" in os.environ: # If other tests set this
            del os.environ["MCP_MAX_RETRIES"]
        if "MCP_REQUEST_TIMEOUT" in os.environ: # If other tests set this
            del os.environ["MCP_REQUEST_TIMEOUT"]


    def test_init_with_env_vars(self):
        """Test MCPClient initialization with environment variables only"""
        client = MCPClient() # No config manager
        self.assertEqual(client.api_key, "test_api_key_env")
        self.assertEqual(client.api_endpoint, "https://test-api.mcp.dev/v1/env")
        self.assertEqual(client.max_retries, 3) # Default
        self.assertEqual(client.request_timeout, 15) # Default

    def test_init_with_direct_params_override_env(self):
        """Test MCPClient initialization with explicit parameters overriding env vars"""
        client = MCPClient(api_key="param_key", api_endpoint="https://param-api.mcp.dev/v1", max_retries=5, request_timeout=20)
        self.assertEqual(client.api_key, "param_key")
        self.assertEqual(client.api_endpoint, "https://param-api.mcp.dev/v1")
        self.assertEqual(client.max_retries, 5)
        self.assertEqual(client.request_timeout, 20)

    def test_init_with_config_manager_full_override(self):
        """Test MCPClient initialization with ConfigManager providing all settings."""
        mock_cm = MagicMock(spec=ConfigManager)
        mock_cm.get.side_effect = lambda key, default=None: {
            'mcp_integration.api_key': "config_api_key",
            'mcp_integration.api_endpoint': "https://config-api.mcp.dev/v1",
            'mcp_integration.max_retries': 10,
            'mcp_integration.request_timeout': 30
        }.get(key, default)

        client = MCPClient(config_manager=mock_cm)
        self.assertEqual(client.api_key, "config_api_key")
        self.assertEqual(client.api_endpoint, "https://config-api.mcp.dev/v1")
        self.assertEqual(client.max_retries, 10)
        self.assertEqual(client.request_timeout, 30)
        
        # Check that config_manager.get was called for each mcp_integration setting
        mock_cm.get.assert_any_call('mcp_integration.api_key')
        mock_cm.get.assert_any_call('mcp_integration.api_endpoint')
        mock_cm.get.assert_any_call('mcp_integration.max_retries', 3) # Default passed to get
        mock_cm.get.assert_any_call('mcp_integration.request_timeout', 15) # Default passed to get


    def test_init_with_config_manager_partial_fallback_to_env(self):
        """Test MCPClient init with ConfigManager (partial), falling back to env vars."""
        mock_cm = MagicMock(spec=ConfigManager)
        mock_cm.get.side_effect = lambda key, default=None: {
            'mcp_integration.api_key': "config_api_key", # Only API key from config
            # api_endpoint, max_retries, request_timeout will be None from config
        }.get(key, default) # if key not in dict, returns default (None)

        client = MCPClient(config_manager=mock_cm)
        self.assertEqual(client.api_key, "config_api_key") # From config
        self.assertEqual(client.api_endpoint, "https://test-api.mcp.dev/v1/env") # Fallback to env
        self.assertEqual(client.max_retries, 3) # Default, as env not set for this
        self.assertEqual(client.request_timeout, 15) # Default, as env not set for this

    def test_init_with_config_manager_and_direct_params_priority(self):
        """Test MCPClient init: direct params > config_manager > env_vars."""
        mock_cm = MagicMock(spec=ConfigManager)
        mock_cm.get.side_effect = lambda key, default=None: {
            'mcp_integration.api_key': "config_api_key",
            'mcp_integration.api_endpoint': "https://config-api.mcp.dev/v1",
            'mcp_integration.max_retries': 10,
        }.get(key, default)

        # Direct param api_key should win over config and env
        # Direct param max_retries should win over config
        # Config endpoint should win over env (as no direct endpoint param)
        # Timeout should fallback to env then default as not in direct or config
        os.environ["MCP_REQUEST_TIMEOUT"] = "25" # Test env fallback for timeout

        client = MCPClient(api_key="direct_api_key", max_retries=5, config_manager=mock_cm)
        
        self.assertEqual(client.api_key, "direct_api_key")
        self.assertEqual(client.api_endpoint, "https://config-api.mcp.dev/v1")
        self.assertEqual(client.max_retries, 5)
        self.assertEqual(client.request_timeout, 25) # From env, then default would be 15


    def test_init_missing_api_key_all_sources(self):
        """Test MCPClient initialization fails if API key is missing from all sources."""
        if "MCP_API_KEY" in os.environ:
            del os.environ["MCP_API_KEY"] # Remove from env
        
        mock_cm = MagicMock(spec=ConfigManager)
        mock_cm.get.return_value = None # Config returns None for api_key

        with self.assertRaisesRegex(ValueError, "MCP API key not provided"):
            MCPClient(config_manager=mock_cm) # No direct param, no env, no config

    @patch('mcp_integration.requests.post')
    def test_make_api_request_success(self, mock_post):
        """Test successful API request using the env-only client"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "print('Hello, MCP!')"}
        mock_post.return_value = mock_response
        
        result = self.client_env_only._make_api_request("test/endpoint", {"param": "value"})
        
        mock_post.assert_called_once_with(
            "https://test-api.mcp.dev/v1/env/test/endpoint", # Uses env endpoint
            headers={
                "Authorization": "Bearer test_api_key_env", # Uses env api key
                "Content-Type": "application/json"
            },
            json={"param": "value"},
            timeout=15 # Default timeout
        )
        self.assertEqual(result, {"code": "print('Hello, MCP!')"})

    @patch('mcp_integration.requests.post')
    def test_make_api_request_error(self, mock_post):
        """Test API request with error response"""
        # Mock the error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # Make the request
        result = self.client_env_only._make_api_request("test/endpoint", {"param": "value"})
        
        # Verify the result is None for error response
        self.assertIsNone(result)

    @patch('mcp_integration.requests.post')
    def test_make_api_request_exception(self, mock_post):
        """Test API request with exception"""
        # Mock an exception
        mock_post.side_effect = Exception("Connection error")
        
        # Mock the retry_with_backoff decorator to pass through the function
        # and not actually apply retries for this test
        with patch('mcp_integration.retry_with_backoff', side_effect=lambda *args, **kwargs: lambda f: f):
            # The method should handle the exception and return None
            result = self.client_env_only._make_api_request("test/endpoint", {"param": "value"})
            self.assertIsNone(result)

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_code_success_with_env_client(self, mock_api_request):
        mock_api_request.return_value = {"code": "def test(): return 'Hello, MCP!'"}
        code = self.client_env_only.generate_code("python")
        self.assertEqual(code, "def test(): return 'Hello, MCP!'")
        mock_api_request.assert_called_once_with(
            "generate/code", 
            {"task": "code_generation", "language": "python", "context": {"purpose": "github-contribution", "complexity": "low"}}
        )

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_code_with_context(self, mock_api_request):
        """Test code generation with custom context"""
        # Mock successful API response
        mock_api_request.return_value = {"code": "def advanced(): return 'Advanced MCP!'"}
        
        # Call the method with custom context
        custom_context = {"purpose": "testing", "complexity": "high"}
        code = self.client_env_only.generate_code("python", custom_context)
        
        # Verify the result
        self.assertEqual(code, "def advanced(): return 'Advanced MCP!'")
        
        # Verify the API request was made with correct parameters
        mock_api_request.assert_called_once_with(
            "generate/code", 
            {
                "task": "code_generation",
                "language": "python",
                "context": custom_context
            }
        )

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_code_api_failure(self, mock_api_request):
        """Test code generation with API failure"""
        # Mock API failure
        mock_api_request.return_value = None
        
        # Call the method
        code = self.client_env_only.generate_code("python")
        
        # Verify fallback code was generated
        self.assertIn("# Generated fallback code", code)
        self.assertIn("def process_data(items):", code)

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_code_api_exception(self, mock_api_request):
        """Test code generation with API exception"""
        # Mock API exception
        mock_api_request.side_effect = Exception("API error")
        
        # Call the method
        code = self.client_env_only.generate_code("python")
        
        # Verify fallback code was generated
        self.assertIn("# Generated fallback code", code)
        self.assertIn("def process_data(items):", code)

    def test_generate_fallback_code_python(self):
        """Test fallback code generation for Python"""
        code = self.client_env_only._generate_fallback_code("python")
        self.assertIn("# Generated fallback code", code)
        self.assertIn("def process_data(items):", code)
        self.assertIn("return results", code)

    def test_generate_fallback_code_javascript(self):
        """Test fallback code generation for JavaScript"""
        code = self.client_env_only._generate_fallback_code("javascript")
        self.assertIn("// Generated fallback code", code)
        self.assertIn("function processData(items)", code)
        self.assertIn("return items.map", code)

    def test_generate_fallback_code_markdown(self):
        """Test fallback code generation for Markdown"""
        code = self.client_env_only._generate_fallback_code("markdown")
        # Check for the new starting string
        self.assertIn("# Fallback Content", code)
        # Keep checks for other expected content
        self.assertIn("- Item 1", code)
        self.assertIn("```", code)

    def test_generate_fallback_code_unknown(self):
        """Test fallback code generation for unknown language"""
        code = self.client_env_only._generate_fallback_code("unknown")
        # Check for the new format
        self.assertIn("Fallback content for unknown generated at", code)

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_commit_message_success_env_client(self, mock_api_request):
        mock_api_request.return_value = {"message": "Add new feature X"}
        changes = [{"file_type": "python", "size": 100, "operation": "add"}]
        message = self.client_env_only.generate_commit_message(changes, "test/repo")
        self.assertEqual(message, "Add new feature X")
        mock_api_request.assert_called_once_with(
            "generate/commit", 
            {"task": "commit_message", "repository": "test/repo", "changes": changes}
        )

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_analyze_repository_success(self, mock_api_request):
        """Test successful repository analysis"""
        # Mock successful API response
        mock_api_request.return_value = {
            "language": "python",
            "patterns": ["camelCase", "docstrings"],
            "recommendations": ["add more tests"]
        }
        
        # Call the method
        repo_data = {"files": ["main.py", "utils.py"], "commits": [{"hash": "abc123"}]}
        result = self.client_env_only.analyze_repository(repo_data)
        
        # Verify the result
        self.assertEqual(result["language"], "python")
        self.assertEqual(result["patterns"], ["camelCase", "docstrings"])
        
        # Verify the API request was made with correct parameters
        mock_api_request.assert_called_once_with(
            "analyze/repository", 
            {
                "task": "repo_analysis",
                "repository_data": repo_data
            }
        )

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_analyze_repository_api_failure(self, mock_api_request):
        """Test repository analysis with API failure"""
        # Mock API failure
        mock_api_request.return_value = None
        
        # Call the method
        repo_data = {"files": ["main.py", "utils.py"]}
        result = self.client_env_only.analyze_repository(repo_data)
        
        # Verify empty dict was returned
        self.assertEqual(result, {})

    def test_get_mcp_client_no_config_uses_env(self):
        """Test get_mcp_client uses environment variables when no ConfigManager is passed."""
        client = get_mcp_client()
        self.assertIsInstance(client, MCPClient)
        self.assertEqual(client.api_key, "test_api_key_env")
        self.assertEqual(client.api_endpoint, "https://test-api.mcp.dev/v1/env")

    def test_get_mcp_client_with_config_full_override(self):
        """Test get_mcp_client uses ConfigManager for all settings."""
        mock_cm = MagicMock(spec=ConfigManager)
        mock_cm.get.side_effect = lambda key, default=None: {
            'mcp_integration.api_key': "config_api_key_getter",
            'mcp_integration.api_endpoint': "https://config-api.mcp.dev/v1/getter",
            'mcp_integration.max_retries': 12,
            'mcp_integration.request_timeout': 32
        }.get(key, default)

        client = get_mcp_client(config_manager=mock_cm)
        self.assertIsInstance(client, MCPClient)
        self.assertEqual(client.api_key, "config_api_key_getter")
        self.assertEqual(client.api_endpoint, "https://config-api.mcp.dev/v1/getter")
        self.assertEqual(client.max_retries, 12)
        self.assertEqual(client.request_timeout, 32)

    def test_get_mcp_client_with_config_partial_fallback_to_env(self):
        """Test get_mcp_client uses ConfigManager (partial) and falls back to env."""
        mock_cm = MagicMock(spec=ConfigManager)
        mock_cm.get.side_effect = lambda key, default=None: {
            'mcp_integration.api_key': "config_api_key_getter_partial", # Only API key from config
            # api_endpoint, max_retries, request_timeout will be None from config get calls
        }.get(key, default)

        # Set specific env vars for other fallbacks if not already set by global setUp
        os.environ["MCP_MAX_RETRIES"] = "7"
        
        client = get_mcp_client(config_manager=mock_cm)
        self.assertIsInstance(client, MCPClient)
        self.assertEqual(client.api_key, "config_api_key_getter_partial") # From config
        self.assertEqual(client.api_endpoint, "https://test-api.mcp.dev/v1/env") # Fallback to env
        self.assertEqual(client.max_retries, 7) # Fallback to env (then default is 3)
        self.assertEqual(client.request_timeout, 15) # Default (env not set for this, then default is 15)


    def test_get_mcp_client_missing_api_key_all_sources(self):
        """Test get_mcp_client returns None if API key is missing everywhere."""
        if "MCP_API_KEY" in os.environ:
            del os.environ["MCP_API_KEY"]
        
        mock_cm = MagicMock(spec=ConfigManager)
        # Configure mock_cm.get to return None for 'mcp_integration.api_key'
        # and other mcp keys to simulate them not being in config
        def mock_get_side_effect(key, default=None):
            if key == 'mcp_integration.api_key':
                return None 
            # for other mcp keys, return None to ensure they don't accidentally provide one
            elif key.startswith('mcp_integration.'): 
                return None
            return default
        mock_cm.get.side_effect = mock_get_side_effect
        
        client = get_mcp_client(config_manager=mock_cm)
        self.assertIsNone(client)

    def test_get_mcp_client_is_singleton(self):
        """Test get_mcp_client returns the same instance on multiple calls."""
        client1 = get_mcp_client()
        client2 = get_mcp_client()
        self.assertIs(client1, client2)

        # With config manager
        patch('mcp_integration._mcp_client_instance', None).start() # Reset for this part
        mock_cm = MagicMock(spec=ConfigManager)
        mock_cm.get.return_value = "dummy_value_to_force_creation" # Ensure it tries to create
        
        client_cm1 = get_mcp_client(config_manager=mock_cm)
        client_cm2 = get_mcp_client(config_manager=mock_cm)
        self.assertIsNotNone(client_cm1) # Make sure it created an instance
        self.assertIs(client_cm1, client_cm2)
        patch.stopall() # Important to stop patches started within a test method


if __name__ == '__main__':
    unittest.main() 