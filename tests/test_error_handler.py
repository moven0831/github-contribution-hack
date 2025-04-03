"""
Unit tests for error_handler.py
"""
import unittest
import logging
from unittest.mock import patch, MagicMock, Mock
import sys
import requests
import pytest

# Add parent directory to path so we can import modules
sys.path.insert(0, '.')

from error_handler import (
    ContributionError, 
    ConfigurationError, 
    NetworkError, 
    APIError, 
    AuthenticationError,
    GitError, 
    TimeoutError,
    ErrorCategory,
    get_error_category,
    create_error_from_exception,
    handle_error,
    safe_operation
)

class TestErrorCategories(unittest.TestCase):
    """Test error category functionality"""
    
    def test_error_category_values(self):
        """Test that all error categories have the expected values"""
        self.assertEqual(ErrorCategory.CONFIGURATION, "configuration")
        self.assertEqual(ErrorCategory.NETWORK, "network")
        self.assertEqual(ErrorCategory.API, "api")
        self.assertEqual(ErrorCategory.AUTHENTICATION, "authentication")
        self.assertEqual(ErrorCategory.PERMISSION, "permission")
        self.assertEqual(ErrorCategory.INPUT_VALIDATION, "input_validation")
        self.assertEqual(ErrorCategory.TIMEOUT, "timeout")
        self.assertEqual(ErrorCategory.GIT, "git")
        self.assertEqual(ErrorCategory.RUNTIME, "runtime")
        self.assertEqual(ErrorCategory.UNKNOWN, "unknown")

class TestBaseContributionError(unittest.TestCase):
    """Test ContributionError base class"""
    
    def test_basic_error(self):
        """Test basic error creation"""
        error = ContributionError("Test error")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.category, ErrorCategory.UNKNOWN)
        self.assertEqual(error.details, {})
        self.assertIsNone(error.recovery_hint)
        self.assertIsNone(error.original_exception)
    
    def test_error_with_all_params(self):
        """Test error with all parameters specified"""
        original_exc = ValueError("Original error")
        error = ContributionError(
            message="Test error",
            category=ErrorCategory.CONFIGURATION,
            details={"param": "value"},
            recovery_hint="Try this to fix it",
            original_exception=original_exc
        )
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.category, ErrorCategory.CONFIGURATION)
        self.assertEqual(error.details, {"param": "value"})
        self.assertEqual(error.recovery_hint, "Try this to fix it")
        self.assertEqual(error.original_exception, original_exc)
    
    def test_error_includes_recovery_hint_in_str(self):
        """Test that str representation includes recovery hint"""
        error = ContributionError(
            message="Test error",
            recovery_hint="Try this to fix it"
        )
        
        self.assertIn("Test error", str(error))
        self.assertIn("Try this to fix it", str(error))
    
    def test_to_dict_method(self):
        """Test to_dict serialization method"""
        original_exc = ValueError("Original error")
        error = ContributionError(
            message="Test error",
            category=ErrorCategory.CONFIGURATION,
            details={"param": "value"},
            recovery_hint="Try this to fix it",
            original_exception=original_exc
        )
        
        error_dict = error.to_dict()
        
        self.assertEqual(error_dict["error"], "ContributionError")
        self.assertEqual(error_dict["message"], "Test error")
        self.assertEqual(error_dict["category"], ErrorCategory.CONFIGURATION)
        self.assertEqual(error_dict["details"], {"param": "value"})
        self.assertEqual(error_dict["recovery_hint"], "Try this to fix it")
        self.assertEqual(error_dict["original_error"], str(original_exc))
        self.assertEqual(error_dict["original_type"], "ValueError")

class TestSpecificErrorClasses(unittest.TestCase):
    """Test specific error subclasses"""
    
    def test_configuration_error(self):
        """Test ConfigurationError class"""
        error = ConfigurationError("Config error")
        self.assertEqual(error.category, ErrorCategory.CONFIGURATION)
        self.assertEqual(error.message, "Config error")
    
    def test_network_error(self):
        """Test NetworkError class"""
        error = NetworkError("Network error")
        self.assertEqual(error.category, ErrorCategory.NETWORK)
        self.assertEqual(error.message, "Network error")
    
    def test_api_error_basic(self):
        """Test basic APIError class"""
        error = APIError("API error")
        self.assertEqual(error.category, ErrorCategory.API)
        self.assertEqual(error.message, "API error")
        self.assertEqual(error.details, {})
    
    def test_api_error_with_details(self):
        """Test APIError with status code and endpoint"""
        error = APIError(
            message="API error", 
            status_code=404, 
            endpoint="/api/test"
        )
        self.assertEqual(error.category, ErrorCategory.API)
        self.assertEqual(error.message, "API error")
        self.assertEqual(error.details["status_code"], 404)
        self.assertEqual(error.details["endpoint"], "/api/test")
    
    def test_authentication_error(self):
        """Test AuthenticationError class"""
        error = AuthenticationError("Auth error")
        self.assertEqual(error.category, ErrorCategory.AUTHENTICATION)
        self.assertEqual(error.message, "Auth error")
    
    def test_git_error(self):
        """Test GitError class"""
        error = GitError("Git error")
        self.assertEqual(error.category, ErrorCategory.GIT)
        self.assertEqual(error.message, "Git error")
    
    def test_timeout_error(self):
        """Test TimeoutError class"""
        error = TimeoutError("Timeout error")
        self.assertEqual(error.category, ErrorCategory.TIMEOUT)
        self.assertEqual(error.message, "Timeout error")
        self.assertEqual(error.details, {})
    
    def test_timeout_error_with_value(self):
        """Test TimeoutError with timeout value"""
        error = TimeoutError("Timeout error", timeout_value=30)
        self.assertEqual(error.category, ErrorCategory.TIMEOUT)
        self.assertEqual(error.message, "Timeout error")
        self.assertEqual(error.details["timeout_value"], 30)

class TestErrorCategorization(unittest.TestCase):
    """Test error categorization functions"""
    
    def test_get_error_category_for_standard_errors(self):
        """Test categorization of standard Python errors"""
        self.assertEqual(get_error_category(ValueError("test")), ErrorCategory.INPUT_VALIDATION)
        self.assertEqual(get_error_category(TypeError("test")), ErrorCategory.INPUT_VALIDATION)
        self.assertEqual(get_error_category(KeyError("test")), ErrorCategory.CONFIGURATION)
        self.assertEqual(get_error_category(FileNotFoundError("test")), ErrorCategory.CONFIGURATION)
        self.assertEqual(get_error_category(PermissionError("test")), ErrorCategory.PERMISSION)
        self.assertEqual(get_error_category(ConnectionError("test")), ErrorCategory.NETWORK)
        self.assertEqual(get_error_category(TimeoutError("test")), ErrorCategory.TIMEOUT)
    
    def test_get_error_category_for_custom_errors(self):
        """Test categorization of our custom errors"""
        self.assertEqual(get_error_category(ConfigurationError("test")), ErrorCategory.CONFIGURATION)
        self.assertEqual(get_error_category(NetworkError("test")), ErrorCategory.NETWORK)
        self.assertEqual(get_error_category(APIError("test")), ErrorCategory.API)
    
    def test_get_error_category_for_requests_errors(self):
        """Test categorization of requests library errors"""
        self.assertEqual(get_error_category(requests.ConnectionError("test")), ErrorCategory.NETWORK)
        self.assertEqual(get_error_category(requests.Timeout("test")), ErrorCategory.TIMEOUT)
        self.assertEqual(get_error_category(requests.RequestException("test")), ErrorCategory.API)
    
    def test_get_error_category_unknown(self):
        """Test categorization of unknown error types"""
        class CustomUnknownError(Exception):
            pass
        
        self.assertEqual(get_error_category(CustomUnknownError()), ErrorCategory.UNKNOWN)

class TestCreateErrorFromException(unittest.TestCase):
    """Test create_error_from_exception function"""
    
    def test_create_from_standard_exception(self):
        """Test creating error from standard exception"""
        original = ValueError("Invalid value")
        error = create_error_from_exception(original)
        
        self.assertIsInstance(error, ContributionError)
        self.assertEqual(error.category, ErrorCategory.INPUT_VALIDATION)
        self.assertEqual(error.message, "Invalid value")
        self.assertEqual(error.original_exception, original)
    
    def test_create_with_custom_message(self):
        """Test creating error with custom message"""
        original = ValueError("Invalid value")
        error = create_error_from_exception(original, message="Custom error message")
        
        self.assertIsInstance(error, ContributionError)
        self.assertEqual(error.message, "Custom error message")
        self.assertEqual(error.original_exception, original)
    
    def test_passthrough_contribution_error(self):
        """Test that ContributionError instances are passed through"""
        original = ConfigurationError("Config error")
        error = create_error_from_exception(original)
        
        self.assertIs(error, original)  # Should be the same object

class TestHandleError(unittest.TestCase):
    """Test handle_error function"""
    
    @patch('error_handler.logger')
    def test_handle_error_logging(self, mock_logger):
        """Test that handle_error logs appropriately"""
        exc = ValueError("Test error")
        handle_error(exc, log_level=logging.ERROR, reraise=False)
        
        mock_logger.log.assert_called_once()
        args = mock_logger.log.call_args[0]
        self.assertEqual(args[0], logging.ERROR)
        self.assertIn("Test error", args[1])
    
    def test_handle_error_reraise(self):
        """Test that handle_error reraises when configured"""
        with self.assertRaises(ContributionError):
            handle_error(ValueError("Test error"), reraise=True)
    
    def test_handle_error_no_reraise(self):
        """Test that handle_error doesn't reraise when configured"""
        result = handle_error(ValueError("Test error"), reraise=False)
        self.assertIsInstance(result, ContributionError)
    
    @patch('error_handler.logger')
    def test_handle_error_with_custom_message(self, mock_logger):
        """Test handle_error with custom error message"""
        exc = ValueError("Original error")
        error = handle_error(exc, error_message="Custom error message", reraise=False)
        
        self.assertEqual(error.message, "Custom error message")
        mock_logger.log.assert_called_once()
        args = mock_logger.log.call_args[0]
        self.assertIn("Custom error message", args[1])

class TestSafeOperation(unittest.TestCase):
    """Test safe_operation decorator"""
    
    @patch('error_handler.handle_error')
    def test_safe_operation_success(self, mock_handle_error):
        """Test safe_operation with successful function"""
        @safe_operation()
        def test_func():
            return "success"
        
        result = test_func()
        self.assertEqual(result, "success")
        mock_handle_error.assert_not_called()
    
    @patch('error_handler.handle_error')
    def test_safe_operation_exception(self, mock_handle_error):
        """Test safe_operation with function that raises exception"""
        mock_handle_error.return_value = ContributionError("Handled error")
        
        @safe_operation(reraise=False, fallback_result="fallback")
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        self.assertEqual(result, "fallback")
        mock_handle_error.assert_called_once()
    
    @patch('error_handler.handle_error')
    def test_safe_operation_custom_message(self, mock_handle_error):
        """Test safe_operation with custom error message"""
        mock_handle_error.return_value = ContributionError("Handled error")
        
        @safe_operation(error_message="Custom message", reraise=False)
        def test_func():
            raise ValueError("Test error")
        
        test_func()
        mock_handle_error.assert_called_once()
        kwargs = mock_handle_error.call_args[1]
        self.assertEqual(kwargs["error_message"], "Custom message")
    
    @patch('error_handler.handle_error')
    def test_safe_operation_preserves_function_metadata(self, mock_handle_error):
        """Test that safe_operation preserves function metadata"""
        @safe_operation()
        def test_func(arg1, arg2=None):
            """Test docstring"""
            return arg1, arg2
        
        self.assertEqual(test_func.__name__, "test_func")
        self.assertEqual(test_func.__doc__, "Test docstring")
        result = test_func("value", arg2="kwarg")
        self.assertEqual(result, ("value", "kwarg"))

if __name__ == "__main__":
    unittest.main() 