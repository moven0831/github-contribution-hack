"""
Tests for retry functionality
"""
import pytest
from unittest.mock import patch, Mock, call
import time
from retry import RetryWithBackoff, RetryableError


@pytest.fixture
def mock_function():
    """Create a mock function that fails a specified number of times"""
    def create_mock(fail_times=3, exception=RetryableError):
        mock = Mock()
        mock.side_effect = [exception("Test error")] * fail_times + ["success"]
        return mock
    return create_mock


@pytest.mark.unit
def test_retry_with_backoff_success():
    """Test successful retry after failures"""
    # Create a function that fails twice then succeeds
    test_func = Mock()
    test_func.side_effect = [RetryableError("Error 1"), RetryableError("Error 2"), "success"]
    
    # Create retry wrapper
    retry_wrapper = RetryWithBackoff(max_retries=3, base_delay=0.01)
    
    # Wrap and call function
    wrapped_func = retry_wrapper(test_func)
    result = wrapped_func("test_arg", kwarg="test_kwarg")
    
    # Verify result and call count
    assert result == "success"
    assert test_func.call_count == 3
    assert test_func.call_args_list == [
        call("test_arg", kwarg="test_kwarg"),
        call("test_arg", kwarg="test_kwarg"),
        call("test_arg", kwarg="test_kwarg")
    ]


@pytest.mark.unit
def test_retry_with_backoff_max_retries_exceeded():
    """Test that retry stops after max_retries and raises the last exception"""
    # Create a function that always fails
    test_func = Mock()
    test_func.side_effect = RetryableError("Persistent error")
    
    # Create retry wrapper with limited retries
    retry_wrapper = RetryWithBackoff(max_retries=3, base_delay=0.01)
    
    # Wrap function and expect exception
    wrapped_func = retry_wrapper(test_func)
    
    with pytest.raises(RetryableError, match="Persistent error"):
        wrapped_func()
    
    # Verify call count matches max retries + 1 (initial attempt)
    assert test_func.call_count == 4


@pytest.mark.unit
def test_retry_with_backoff_delay_calculation():
    """Test that retry uses exponential backoff for delays"""
    test_func = Mock()
    test_func.side_effect = [RetryableError("Error")] * 3 + ["success"]
    
    # Patch time.sleep to check delay values
    with patch('time.sleep') as mock_sleep:
        # Create retry wrapper with known parameters for predictable delays
        retry_wrapper = RetryWithBackoff(max_retries=3, base_delay=0.1, backoff_factor=2)
        wrapped_func = retry_wrapper(test_func)
        result = wrapped_func()
        
        # Verify correct sleep times (exponential backoff)
        assert mock_sleep.call_count == 3
        assert mock_sleep.call_args_list[0] == call(0.1)  # First retry: base_delay
        assert mock_sleep.call_args_list[1] == call(0.2)  # Second retry: base_delay * backoff_factor
        assert mock_sleep.call_args_list[2] == call(0.4)  # Third retry: base_delay * backoff_factor^2


@pytest.mark.unit
def test_retry_with_backoff_jitter():
    """Test that jitter is applied to delay times"""
    test_func = Mock()
    test_func.side_effect = [RetryableError("Error")] * 3 + ["success"]
    
    # Patch random.uniform to return consistent values
    with patch('random.uniform', return_value=0.5) as mock_uniform, \
         patch('time.sleep') as mock_sleep:
        
        # Create retry wrapper with jitter
        retry_wrapper = RetryWithBackoff(max_retries=3, base_delay=0.1, jitter=True)
        wrapped_func = retry_wrapper(test_func)
        result = wrapped_func()
        
        # Verify random.uniform was called for jitter calculation
        assert mock_uniform.call_count == 3
        
        # With our mock returning 0.5, each delay should be multiplied by 0.5
        assert mock_sleep.call_count == 3
        assert mock_sleep.call_args_list[0] == call(0.05)  # First retry: base_delay * 0.5
        assert mock_sleep.call_args_list[1] == call(0.05)  # Second retry: base_delay * 0.5
        assert mock_sleep.call_args_list[2] == call(0.05)  # Third retry: base_delay * 0.5


@pytest.mark.unit
def test_retry_with_non_retryable_error():
    """Test that non-retryable errors are raised immediately"""
    # Create a function that raises a non-retryable error
    test_func = Mock()
    test_func.side_effect = ValueError("Non-retryable error")
    
    # Create retry wrapper
    retry_wrapper = RetryWithBackoff(max_retries=3, base_delay=0.01)
    wrapped_func = retry_wrapper(test_func)
    
    # Expect the ValueError to be raised immediately
    with pytest.raises(ValueError, match="Non-retryable error"):
        wrapped_func()
    
    # Verify function was only called once (no retries for non-retryable errors)
    assert test_func.call_count == 1


@pytest.mark.unit
def test_retry_with_custom_retryable_errors():
    """Test retry with custom exception types"""
    # Create a function that raises custom exceptions
    test_func = Mock()
    test_func.side_effect = [
        ValueError("Custom error 1"), 
        TypeError("Custom error 2"), 
        "success"
    ]
    
    # Create retry wrapper with custom retryable errors
    retry_wrapper = RetryWithBackoff(
        max_retries=3, 
        base_delay=0.01,
        retryable_exceptions=(ValueError, TypeError)
    )
    wrapped_func = retry_wrapper(test_func)
    
    # Call and verify success after retries
    result = wrapped_func()
    assert result == "success"
    assert test_func.call_count == 3


@pytest.mark.unit
def test_retry_with_on_retry_callback():
    """Test that on_retry callback is called for each retry"""
    # Create a function that fails twice then succeeds
    test_func = Mock()
    test_func.side_effect = [RetryableError("Error 1"), RetryableError("Error 2"), "success"]
    
    # Create on_retry callback
    on_retry_callback = Mock()
    
    # Create retry wrapper with callback
    retry_wrapper = RetryWithBackoff(
        max_retries=3, 
        base_delay=0.01,
        on_retry=on_retry_callback
    )
    wrapped_func = retry_wrapper(test_func)
    
    # Call function
    result = wrapped_func()
    
    # Verify callback was called for each retry
    assert on_retry_callback.call_count == 2
    
    # Verify callback received the correct arguments
    assert isinstance(on_retry_callback.call_args_list[0][0][0], RetryableError)
    assert on_retry_callback.call_args_list[0][0][1] == 1  # First retry attempt
    assert isinstance(on_retry_callback.call_args_list[1][0][0], RetryableError)
    assert on_retry_callback.call_args_list[1][0][1] == 2  # Second retry attempt 