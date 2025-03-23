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


class TestMCPClient(unittest.TestCase):
    """Test cases for the MCPClient class"""

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

    def test_init_with_env_vars(self):
        """Test initialization with environment variables"""
        self.assertEqual(self.client.api_key, "test_api_key")
        self.assertEqual(self.client.api_endpoint, "https://test-api.mcp.dev/v1")

    def test_init_with_params(self):
        """Test initialization with explicit parameters"""
        client = MCPClient(api_key="param_key", api_endpoint="https://param-api.mcp.dev/v1")
        self.assertEqual(client.api_key, "param_key")
        self.assertEqual(client.api_endpoint, "https://param-api.mcp.dev/v1")

    def test_init_missing_api_key(self):
        """Test initialization with missing API key"""
        if "MCP_API_KEY" in os.environ:
            del os.environ["MCP_API_KEY"]
        
        with self.assertRaises(ValueError):
            MCPClient()

    @patch('mcp_integration.requests.post')
    def test_make_api_request_success(self, mock_post):
        """Test successful API request"""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "print('Hello, MCP!')"}
        mock_post.return_value = mock_response
        
        # Make the request
        result = self.client._make_api_request("test/endpoint", {"param": "value"})
        
        # Verify the request was made correctly
        mock_post.assert_called_once_with(
            "https://test-api.mcp.dev/v1/test/endpoint",
            headers={
                "Authorization": "Bearer test_api_key",
                "Content-Type": "application/json"
            },
            json={"param": "value"},
            timeout=30
        )
        
        # Verify the result
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
        result = self.client._make_api_request("test/endpoint", {"param": "value"})
        
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
            result = self.client._make_api_request("test/endpoint", {"param": "value"})
            self.assertIsNone(result)

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_code_success(self, mock_api_request):
        """Test successful code generation"""
        # Mock successful API response
        mock_api_request.return_value = {"code": "def test(): return 'Hello, MCP!'"}
        
        # Call the method
        code = self.client.generate_code("python")
        
        # Verify the result
        self.assertEqual(code, "def test(): return 'Hello, MCP!'")
        
        # Verify the API request was made with correct parameters
        mock_api_request.assert_called_once_with(
            "generate/code", 
            {
                "task": "code_generation",
                "language": "python",
                "context": {"purpose": "github-contribution", "complexity": "low"}
            }
        )

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_code_with_context(self, mock_api_request):
        """Test code generation with custom context"""
        # Mock successful API response
        mock_api_request.return_value = {"code": "def advanced(): return 'Advanced MCP!'"}
        
        # Call the method with custom context
        custom_context = {"purpose": "testing", "complexity": "high"}
        code = self.client.generate_code("python", custom_context)
        
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
        code = self.client.generate_code("python")
        
        # Verify fallback code was generated
        self.assertIn("# Generated fallback code", code)
        self.assertIn("def process_data(items):", code)

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_code_api_exception(self, mock_api_request):
        """Test code generation with API exception"""
        # Mock API exception
        mock_api_request.side_effect = Exception("API error")
        
        # Call the method
        code = self.client.generate_code("python")
        
        # Verify fallback code was generated
        self.assertIn("# Generated fallback code", code)
        self.assertIn("def process_data(items):", code)

    def test_generate_fallback_code_python(self):
        """Test fallback code generation for Python"""
        code = self.client._generate_fallback_code("python")
        self.assertIn("# Generated fallback code", code)
        self.assertIn("def process_data(items):", code)
        self.assertIn("return results", code)

    def test_generate_fallback_code_javascript(self):
        """Test fallback code generation for JavaScript"""
        code = self.client._generate_fallback_code("javascript")
        self.assertIn("// Generated fallback code", code)
        self.assertIn("function processData(items)", code)
        self.assertIn("return items.map", code)

    def test_generate_fallback_code_markdown(self):
        """Test fallback code generation for Markdown"""
        code = self.client._generate_fallback_code("markdown")
        self.assertIn("# Generated Markdown Content", code)
        self.assertIn("## Summary", code)
        self.assertIn("## Features", code)
        self.assertIn("## Example Code", code)

    def test_generate_fallback_code_unknown(self):
        """Test fallback code generation for unknown language"""
        code = self.client._generate_fallback_code("unknown")
        self.assertIn("Generated content at", code)

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_commit_message_success(self, mock_api_request):
        """Test successful commit message generation"""
        # Mock successful API response
        mock_api_request.return_value = {"message": "Add new feature X"}
        
        # Call the method
        changes = [{"file_type": "python", "size": 100, "operation": "add"}]
        message = self.client.generate_commit_message(changes, "test/repo")
        
        # Verify the result
        self.assertEqual(message, "Add new feature X")
        
        # Verify the API request was made with correct parameters
        mock_api_request.assert_called_once_with(
            "generate/commit", 
            {
                "task": "commit_message",
                "repository": "test/repo",
                "changes": changes
            }
        )

    @patch('mcp_integration.MCPClient._make_api_request')
    def test_generate_commit_message_api_failure(self, mock_api_request):
        """Test commit message generation with API failure"""
        # Mock API failure
        mock_api_request.return_value = None
        
        # Call the method
        changes = [{"file_type": "python", "size": 100, "operation": "add"}]
        message = self.client.generate_commit_message(changes, "test/repo")
        
        # Verify fallback message was generated
        self.assertIn("Update code in test/repo at", message)

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
        result = self.client.analyze_repository(repo_data)
        
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
        result = self.client.analyze_repository(repo_data)
        
        # Verify empty dict was returned
        self.assertEqual(result, {})

    def test_get_mcp_client(self):
        """Test get_mcp_client factory function"""
        client = get_mcp_client()
        self.assertIsInstance(client, MCPClient)
        self.assertEqual(client.api_key, "test_api_key")
        self.assertEqual(client.api_endpoint, "https://test-api.mcp.dev/v1")


if __name__ == '__main__':
    unittest.main() 