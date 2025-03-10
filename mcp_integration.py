import os
import json
import requests
import random
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Any

class MCPClient:
    """
    Client for Mission Control Protocol (MCP) API integration
    Enables AI-powered code and commit message generation
    """
    
    def __init__(self, api_key: str = None, api_endpoint: str = None):
        """
        Initialize the MCP client
        
        :param api_key: MCP API key
        :param api_endpoint: MCP API endpoint
        """
        self.api_key = api_key or os.environ.get("MCP_API_KEY")
        self.api_endpoint = api_endpoint or os.environ.get("MCP_API_ENDPOINT", "https://api.mcp.dev/v1")
        
        if not self.api_key:
            raise ValueError("MCP API key not provided. Set MCP_API_KEY environment variable or pass directly.")
    
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
        
        try:
            payload = {
                "task": "code_generation",
                "language": language,
                "context": context
            }
            
            response = self._make_api_request("generate/code", payload)
            
            if response and "code" in response:
                return response["code"]
            else:
                # Fallback to simple code if API fails
                return self._generate_fallback_code(language)
                
        except Exception as e:
            print(f"MCP code generation failed: {str(e)}")
            return self._generate_fallback_code(language)
    
    def generate_commit_message(self, changes: List[Dict], repo_name: str) -> str:
        """
        Generate a contextual commit message based on code changes
        
        :param changes: List of file changes with metadata
        :param repo_name: Name of the repository
        :return: Generated commit message
        """
        try:
            payload = {
                "task": "commit_message",
                "repository": repo_name,
                "changes": changes
            }
            
            response = self._make_api_request("generate/commit", payload)
            
            if response and "message" in response:
                return response["message"]
            else:
                # Fallback to generic commit message
                return f"Update code in {repo_name} at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
        except Exception as e:
            print(f"MCP commit message generation failed: {str(e)}")
            return f"Update code in {repo_name} at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    def analyze_repository(self, repo_data: Dict) -> Dict:
        """
        Analyze repository to determine best contribution approach
        
        :param repo_data: Repository data including files, recent commits, etc.
        :return: Analysis results with recommendations
        """
        try:
            payload = {
                "task": "repo_analysis",
                "repository_data": repo_data
            }
            
            response = self._make_api_request("analyze/repository", payload)
            return response or {}
                
        except Exception as e:
            print(f"MCP repository analysis failed: {str(e)}")
            return {}
    
    def _make_api_request(self, endpoint: str, payload: Dict) -> Dict:
        """
        Make an API request to MCP
        
        :param endpoint: API endpoint
        :param payload: Request payload
        :return: Response data
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_endpoint}/{endpoint}"
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"MCP API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"MCP API Request Error: {str(e)}")
            return None
    
    def _generate_fallback_code(self, language: str) -> str:
        """
        Generate fallback code if API fails
        
        :param language: Programming language
        :return: Simple code snippet
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        random_num = random.randint(4, 100)
        
        if language == "python":
            return f"""# Generated fallback code
# Timestamp: {timestamp}

def process_data(items):
    \"\"\"
    Process the given data items
    \"\"\"
    results = []
    for item in items:
        results.append(item * 2)
    return results

# Example usage
data = [1, 2, 3, {random_num}]
print(f"Processing data: {{data}}")
print(f"Result: {{process_data(data)}}")
"""
        elif language == "javascript":
            return f"""// Generated fallback code
// Timestamp: {timestamp}

/**
 * Process the given data items
 * @param {{Array}} items - Items to process
 * @return {{Array}} - Processed items
 */
function processData(items) {{
  return items.map(item => item * 2);
}}

// Example usage
const data = [1, 2, 3, {random_num}];
console.log(`Processing data: ${{data}}`);
console.log(`Result: ${{processData(data)}}`);
"""
        elif language == "markdown":
            return f"""# Project Update

## Latest Changes - {timestamp}

- Added new functionality for data processing
- Fixed bug #{random.randint(100, 999)}
- Updated documentation

## Next Steps

- [ ] Implement advanced features
- [ ] Add more test coverage
- [ ] Review performance metrics
"""
        else:
            return f"Generated content at {timestamp}"


def get_mcp_client() -> MCPClient:
    """
    Get configured MCP client using environment variables
    
    :return: Configured MCP client
    """
    return MCPClient() 