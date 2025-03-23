"""
Pytest configuration file for GitHub Contribution Hack tests
"""
import os
import tempfile
import pytest
import yaml
from unittest.mock import Mock, patch
import sys

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def temp_config_file():
    """Create a temporary config file with test settings"""
    temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
    
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
    
    with open(temp_config.name, 'w') as f:
        yaml.dump(config_data, f)
    
    yield temp_config.name
    
    # Cleanup
    if os.path.exists(temp_config.name):
        os.unlink(temp_config.name)


@pytest.fixture
def mock_environment():
    """Set up mock environment variables"""
    original_environ = os.environ.copy()
    
    # Set test environment variables
    os.environ["MCP_API_KEY"] = "test_api_key"
    os.environ["GITHUB_TOKEN"] = "test_github_token"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_environ)


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client"""
    mock_client = Mock()
    
    # Setup common methods
    mock_client.generate_code.return_value = "print('Hello, World!')"
    mock_client.analyze_repository.return_value = {
        "languages": {"python": 0.8, "markdown": 0.2},
        "complexity": "medium",
        "activity": "moderate"
    }
    mock_client.generate_commit_message.return_value = "Add new feature"
    
    return mock_client


@pytest.fixture
def github_hack_patches():
    """Apply common patches for GitHubContributionHack tests"""
    # Import here to avoid circular imports
    from main import GitHubContributionHack
    
    patches = []
    mocks = {}
    
    # Patch environment validation
    validate_patch = patch.object(GitHubContributionHack, '_validate_environment')
    mocks['validate'] = validate_patch.start()
    patches.append(validate_patch)
    
    # Patch credential setup
    creds_patch = patch.object(GitHubContributionHack, '_setup_secure_credentials')
    mocks['creds'] = creds_patch.start()
    patches.append(creds_patch)
    
    # Add missing methods to the class for testing
    def mock_configure_repository_access(self):
        self.g = Mock()
        return
    
    def mock_setup_github_verification(self):
        return
    
    # Save original methods if they exist
    original_methods = {}
    if hasattr(GitHubContributionHack, '_configure_repository_access'):
        original_methods['_configure_repository_access'] = GitHubContributionHack._configure_repository_access
    
    if hasattr(GitHubContributionHack, '_setup_github_verification'):
        original_methods['_setup_github_verification'] = GitHubContributionHack._setup_github_verification
    
    # Apply mock methods
    GitHubContributionHack._configure_repository_access = mock_configure_repository_access
    GitHubContributionHack._setup_github_verification = mock_setup_github_verification
    
    # Patch commit pattern model
    pattern_patch = patch.object(GitHubContributionHack, '_load_commit_pattern_model')
    mocks['pattern'] = pattern_patch.start()
    mocks['pattern'].return_value = None
    patches.append(pattern_patch)
    
    # Patch ContributionAnalytics
    analytics_patch = patch('main.ContributionAnalytics')
    mocks['analytics'] = analytics_patch.start()
    mocks['analytics'].return_value = Mock()
    patches.append(analytics_patch)
    
    yield mocks
    
    # Stop all patches
    for p in patches:
        p.stop()
    
    # Restore original methods
    for method_name, method in original_methods.items():
        setattr(GitHubContributionHack, method_name, method) 