import os
import json
import requests
import random
import logging
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Any
import time

# Import our retry module
from retry import retry_with_backoff, RetryableHTTP
from config_loader import ConfigManager

# Configure logger
logger = logging.getLogger(__name__)

# Create a session for connection pooling
def get_session():
    """Get or create a requests session with proper connection pooling"""
    if not hasattr(get_session, '_session'):
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0  # We handle retries ourselves
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        get_session._session = session
    return get_session._session

class MCPClient:
    """
    Client for Mission Control Protocol (MCP) API integration
    Enables AI-powered code and commit message generation
    """
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None, 
                 max_retries: Optional[int] = None, # Allow None for direct params
                 request_timeout: Optional[int] = None, # Allow None for direct params
                 config_manager: Optional[ConfigManager] = None):
        """
        Initialize the MCP client
        
        Priority Order: Direct Param > ConfigManager > Environment Variable > Default

        :param api_key: MCP API key
        :param api_endpoint: MCP API endpoint
        :param max_retries: Maximum number of retries for API calls
        :param request_timeout: Timeout for API requests in seconds
        :param config_manager: Optional ConfigManager instance
        """
        
        # Determine final values based on priority
        final_api_key = api_key
        final_api_endpoint = api_endpoint
        final_max_retries = max_retries
        final_request_timeout = request_timeout
        
        config_api_key = None
        config_api_endpoint = None
        config_max_retries = None
        config_request_timeout = None

        if config_manager:
            config_api_key = config_manager.get('mcp_integration.api_key')
            config_api_endpoint = config_manager.get('mcp_integration.api_endpoint')
            config_max_retries = config_manager.get('mcp_integration.max_retries')
            config_request_timeout = config_manager.get('mcp_integration.request_timeout')

        # API Key: Param > Config > Env > (Error if None)
        if final_api_key is None:
            final_api_key = config_api_key
        if final_api_key is None:
            final_api_key = os.environ.get("MCP_API_KEY")
        
        # API Endpoint: Param > Config > Env > Default
        default_endpoint = "https://api.mcp.dev/v1"
        if final_api_endpoint is None:
            final_api_endpoint = config_api_endpoint
        if final_api_endpoint is None:
             final_api_endpoint = os.environ.get("MCP_API_ENDPOINT")
        if final_api_endpoint is None:
            final_api_endpoint = default_endpoint

        # Max Retries: Param > Config > Env > Default
        default_max_retries = 3
        if final_max_retries is None:
            final_max_retries = config_max_retries
        if final_max_retries is None:
            env_retries = os.environ.get("MCP_MAX_RETRIES")
            if env_retries is not None:
                try:
                    final_max_retries = int(env_retries)
                except ValueError:
                    logger.warning(f"Invalid value for MCP_MAX_RETRIES environment variable: '{env_retries}'. Using default.")
        if final_max_retries is None:
             final_max_retries = default_max_retries

        # Request Timeout: Param > Config > Env > Default
        default_request_timeout = 15
        if final_request_timeout is None:
            final_request_timeout = config_request_timeout
        if final_request_timeout is None:
            env_timeout = os.environ.get("MCP_REQUEST_TIMEOUT")
            if env_timeout is not None:
                try:
                    final_request_timeout = int(env_timeout)
                except ValueError:
                     logger.warning(f"Invalid value for MCP_REQUEST_TIMEOUT environment variable: '{env_timeout}'. Using default.")
        if final_request_timeout is None:
             final_request_timeout = default_request_timeout
        
        # Assign final values to instance attributes
        self.api_key = final_api_key
        self.api_endpoint = final_api_endpoint
        self.max_retries = final_max_retries
        self.request_timeout = final_request_timeout
        
        # Validate API Key
        if not self.api_key:
            logger.error("MCP API key not provided via direct param, config, or MCP_API_KEY environment variable.")
            raise ValueError("MCP API key not provided. Set MCP_API_KEY, configure in config.yml, or pass directly.")
        
        # Cache commonly used data
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"MCP client initialized with endpoint: {self.api_endpoint}")
    
    def generate_code(self, language: str, context: Dict[str, Any] = None) -> str:
        """
        Generate code using MCP
        
        :param language: Programming language to generate code for
        :param context: Additional context for code generation
        :return: Generated code as string
        """
        # Default context if none provided
        if context is None:
            context = {"purpose": "github-contribution", "complexity": "low"}
        
        logger.debug(f"Generating code for language: {language}")
        try:
            payload = {
                "task": "code_generation",
                "language": language,
                "context": context
            }
            
            response = self._make_api_request("generate/code", payload)
            
            if response and "code" in response:
                logger.info(f"Successfully generated {language} code via MCP")
                return response["code"]
            else:
                # Fallback to simple code if API fails
                logger.warning(f"MCP API returned invalid response for code generation, using fallback")
                return self._generate_fallback_code(language)
                
        except Exception as e:
            logger.error(f"MCP code generation failed: {str(e)}", exc_info=True)
            return self._generate_fallback_code(language)
    
    def generate_commit_message(self, changes: List[Dict], repo_name: str) -> str:
        """
        Generate a contextual commit message based on code changes
        
        :param changes: List of file changes with metadata
        :param repo_name: Name of the repository
        :return: Generated commit message
        """
        logger.debug(f"Generating commit message for repo: {repo_name}")
        try:
            payload = {
                "task": "commit_message",
                "repository": repo_name,
                "changes": changes
            }
            
            response = self._make_api_request("generate/commit", payload)
            
            if response and "message" in response:
                logger.info(f"Successfully generated commit message via MCP")
                return response["message"]
            else:
                # Fallback to generic commit message
                fallback_msg = f"Update code in {repo_name} at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                logger.warning(f"MCP API returned invalid response for commit message, using fallback: {fallback_msg}")
                return fallback_msg
                
        except Exception as e:
            fallback_msg = f"Update code in {repo_name} at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            logger.error(f"MCP commit message generation failed: {str(e)}", exc_info=True)
            return fallback_msg
    
    def analyze_repository(self, repo_data: Dict) -> Dict:
        """
        Analyze repository to determine best contribution approach
        
        :param repo_data: Repository data including files, recent commits, etc.
        :return: Analysis results with recommendations
        """
        logger.debug(f"Analyzing repository with {len(repo_data.get('files', []))} files")
        try:
            payload = {
                "task": "repo_analysis",
                "repository_data": repo_data
            }
            
            response = self._make_api_request("analyze/repository", payload)
            if response:
                logger.info("Repository analysis completed successfully")
                return response
            else:
                logger.warning("MCP API returned invalid response for repository analysis")
                return {}
                
        except Exception as e:
            logger.error(f"MCP repository analysis failed: {str(e)}", exc_info=True)
            return {}
    
    # Use a less complex decorator that will work reliably in tests
    def _make_api_request(self, endpoint: str, payload: Dict) -> Dict:
        """
        Make an API request to MCP with retry capability
        
        :param endpoint: API endpoint
        :param payload: Request payload
        :return: Response data
        """
        url = f"{self.api_endpoint}/{endpoint}"
        logger.debug(f"Making API request to: {url}")
        
        # Manual retry implementation for better test control
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Use requests.post directly for compatibility with test mocking
                # This is more testable than using a global session directly
                response = requests.post(
                    url,
                    headers=self._headers,
                    json=payload,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    logger.debug(f"API request to {endpoint} successful")
                    return response.json()
                else:
                    # Check if we should retry based on status code
                    if RetryableHTTP.is_retryable_error(response.status_code):
                        retry_after = RetryableHTTP.calculate_retry_after(
                            response.headers, default_backoff=1.0, max_backoff=60.0
                        )
                        logger.warning(f"Retryable error {response.status_code}. Will retry after {retry_after}s")
                        # Sleep to respect retry-after
                        time.sleep(retry_after)
                        # Continue to next retry
                        retry_count += 1
                        continue
                    
                    logger.error(f"MCP API Error: {response.status_code} - {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"MCP API request timed out after {self.request_timeout} seconds: {endpoint}")
                retry_count += 1
                if retry_count > max_retries:
                    return None
                time.sleep(1.0)  # Simple backoff
                
            except requests.exceptions.ConnectionError as e:
                logger.error(f"MCP API connection error: {endpoint}")
                retry_count += 1
                if retry_count > max_retries:
                    return None
                time.sleep(1.0)  # Simple backoff
                
            except Exception as e:
                logger.error(f"MCP API Request Error: {str(e)}", exc_info=True)
                # For general exceptions, don't retry to prevent test failures
                return None
        
        # If we've exhausted all retries
        return None
    
    def _generate_fallback_code(self, language: str) -> str:
        """
        Generate fallback code when API fails
        
        :param language: Programming language
        :return: Generated code as string
        """
        logger.info(f"Generating fallback code for {language}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Dictionary of templates for different languages
        templates = {
            "python": f"""# Generated fallback code at {timestamp}
def process_data(items):
    \"\"\"
    Process a list of data items
    
    Args:
        items: List of items to process
        
    Returns:
        Processed data
    \"\"\"
    results = []
    for item in items:
        # Simple transformation
        if isinstance(item, (int, float)):
            results.append(item * 2)
        elif isinstance(item, str):
            results.append(item.upper())
        else:
            results.append(None) # Default for other types
    return results

print(f"Fallback Python code generated at {timestamp}")
""",
            "javascript": f"""// Generated fallback code at {timestamp}
function processData(items) {{
    // Process an array of data items
    console.log('Processing items...', items.length);
    return items.map(item => {{
        if (typeof item === 'number') return item * 2;
        if (typeof item === 'string') return item.toUpperCase();
        return null;
    }});
}}

console.log('Fallback JavaScript code generated at {timestamp}');
""",
            "java": f"""// Generated fallback code at {timestamp}
import java.util.List;
import java.util.ArrayList;

public class FallbackProcessor {{
    public List<Object> processData(List<Object> items) {{
        System.out.println("Processing items...");
        List<Object> results = new ArrayList<>();
        for (Object item : items) {{
            if (item instanceof Integer || item instanceof Double) {{
                results.add(((Number)item).doubleValue() * 2);
            }}
            else if (item instanceof String) {{
                results.add(((String)item).toUpperCase());
            }}
            else {{
                results.add(null);
            }}
        }}
        return results;
    }}
}}

// Fallback Java code generated at {timestamp}
""",
            "text": f"Fallback text content generated at {timestamp}.\nThis is a placeholder because the primary content generation service was unavailable.",
            "markdown": f"""# Fallback Content - {timestamp}

This is fallback Markdown content. The main content generation service (MCP) might be unavailable.

- Item 1
- Item 2

```
Some example code or data might go here.
```
"""
        }
        
        return templates.get(language.lower(), f"Fallback content for {language} generated at {timestamp}")

# Global MCP client instance
_mcp_client_instance: Optional[MCPClient] = None

def get_mcp_client(config_manager: Optional[ConfigManager] = None) -> Optional[MCPClient]:
    """
    Get a shared instance of the MCPClient.
    Initializes the client on first call using environment variables or config.
    Uses Priority: ConfigManager > Environment Variable > Default

    Args:
        config_manager: Optional ConfigManager instance to load MCP settings.

    Returns:
        MCPClient instance or None if initialization fails.
    """
    global _mcp_client_instance
    
    if _mcp_client_instance is None:
        try:
            # Determine parameters using Config -> Env -> Default priority
            # Note: MCPClient.__init__ itself now handles Param > Config > Env > Default
            # We just need to gather the inputs for it based on Config > Env > Default for this factory function.
            
            api_key_to_pass = None
            endpoint_to_pass = None
            retries_to_pass = None
            timeout_to_pass = None
            
            if config_manager:
                api_key_to_pass = config_manager.get('mcp_integration.api_key')
                endpoint_to_pass = config_manager.get('mcp_integration.api_endpoint')
                retries_to_pass = config_manager.get('mcp_integration.max_retries')
                timeout_to_pass = config_manager.get('mcp_integration.request_timeout')

            # Fallback to environment variables only if config didn't provide a value
            if api_key_to_pass is None:
                 api_key_to_pass = os.environ.get("MCP_API_KEY")
            if endpoint_to_pass is None:
                 endpoint_to_pass = os.environ.get("MCP_API_ENDPOINT")
            if retries_to_pass is None:
                env_retries = os.environ.get("MCP_MAX_RETRIES")
                if env_retries is not None:
                     try: retries_to_pass = int(env_retries)
                     except ValueError: pass # Ignore invalid env var here, MCPClient init will use default
            if timeout_to_pass is None:
                env_timeout = os.environ.get("MCP_REQUEST_TIMEOUT")
                if env_timeout is not None:
                     try: timeout_to_pass = int(env_timeout)
                     except ValueError: pass # Ignore invalid env var here, MCPClient init will use default

            # Instantiate MCPClient - its internal logic handles defaults if params are None
            # Pass config_manager along so MCPClient can use it if needed (though currently redundant with param passing)
            _mcp_client_instance = MCPClient(
                api_key=api_key_to_pass,
                api_endpoint=endpoint_to_pass,
                max_retries=retries_to_pass,
                request_timeout=timeout_to_pass,
                config_manager=config_manager # Pass original CM if present
            )
            
            logger.info("MCPClient instance created.")

        except ValueError as e: # Handles missing API key from MCPClient init
            logger.error(f"Failed to initialize MCPClient: {e}")
            _mcp_client_instance = None # Ensure it remains None on failure
        except Exception as e:
            logger.error(f"An unexpected error occurred during MCPClient initialization: {e}", exc_info=True)
            _mcp_client_instance = None # Ensure it remains None on failure
            
    return _mcp_client_instance 