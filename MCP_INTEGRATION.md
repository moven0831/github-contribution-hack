# MCP Integration for GitHub Contribution Hack

This document provides detailed information about integrating the GitHub Contribution Hack with MCP (Mission Control Protocol) for enhanced code and commit generation.

## Overview

MCP integration leverages AI-powered code and commit generation to create more realistic, context-aware contributions to your GitHub repositories. This integration enhances the tool with:

- Intelligent, context-aware code generation
- Repository-specific commit messages
- Adaptive content complexity
- File type detection and appropriate naming
- Repository analysis and pattern recognition

## Setup

### Prerequisites

- MCP API key (obtain from [MCP Dashboard](https://mcp.dev/dashboard))
- GitHub Contribution Hack installed and configured

### Configuration

1. **Update Environment Variables**

   Copy `.env.example` to `.env` and set your MCP credentials:
   ```
   # MCP API Integration
   MCP_API_KEY=your_mcp_api_key_here
   MCP_API_ENDPOINT=https://api.mcp.dev/v1
   ```

2. **Enable MCP in config.yml**

   The `config.yml` file contains a dedicated section for MCP settings:
   ```yaml
   # MCP Integration Settings
   mcp_integration:
     enabled: true                            # Master switch to enable/disable MCP
     api_endpoint: "https://api.mcp.dev/v1"   # MCP API endpoint
     complexity: "medium"                     # Code complexity (low, medium, high)
     language_weights:                        # Language distribution
       python: 0.4
       javascript: 0.3
       markdown: 0.2
       text: 0.1
     repository_analysis: true                # Analyze repos for patterns
     content_quality: "high"                  # Quality of generated content
     dry_run: false                           # Test mode (no actual commits)
   ```

## Usage

Once configured, MCP integration works automatically when you run the GitHub Contribution Hack:

```bash
python main.py
```

### Testing MCP Integration

To test MCP integration without making actual commits, enable dry run mode in `config.yml`:

```yaml
mcp_integration:
  enabled: true
  dry_run: true  # Enable this for testing
  # ... other settings
```

This will generate and display content without pushing to GitHub.

## Advanced Configuration

### Language Weighting

Control the distribution of languages in generated content by adjusting weights:

```yaml
language_weights:
  python: 0.6     # More Python code
  javascript: 0.2 # Less JavaScript
  markdown: 0.1   # Even less Markdown
  text: 0.1       # Minimal plain text
```

Weights represent relative probabilities and don't need to sum to 1.

### Complexity Levels

The `complexity` parameter controls sophistication of generated code:

- **low**: Simple functions, basic operations, minimal documentation
- **medium**: Multi-function modules, error handling, comprehensive documentation
- **high**: Advanced patterns, optimized algorithms, extensive documentation

### Content Quality

The `content_quality` parameter controls overall quality metrics:

- **low**: Basic contributions with minimal context
- **medium**: Context-aware contributions with moderate detail
- **high**: Highly contextual, repository-specific content

## Repository Analysis

When `repository_analysis` is enabled, MCP will:

1. Analyze existing repository structure and patterns
2. Identify coding style, naming conventions, and architectural patterns
3. Generate content that matches existing repository style

This creates more authentic and consistent contributions.

## Troubleshooting

### API Connection Issues

If you encounter MCP API connection problems:

1. Verify your API key is correct in `.env`
2. Check your internet connection
3. Ensure the API endpoint is properly configured
4. Test the API directly:
   ```bash
   curl -H "Authorization: Bearer YOUR_MCP_API_KEY" https://api.mcp.dev/v1/ping
   ```

### Fallback Mechanism

If MCP is unavailable, the system will automatically fall back to standard content generation methods:

1. Markov-based generation (if enabled)
2. Basic random content generation

Check the logs for messages indicating fallback has occurred.

## Advanced Use Cases

### Content Customization

For custom content requirements, modify the context sent to MCP in `_generate_mcp_content()` in `main.py`:

```python
context = {
    "purpose": "github-contribution",
    "complexity": self.config.get('mcp_integration', {}).get('complexity', 'low'),
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "custom_field": "your_custom_value"  # Add custom context
}
```

### Integration with CI/CD

To run MCP-powered contributions as part of CI/CD:

1. Set up environment variables in your CI/CD environment
2. Create a scheduled job that runs `python main.py`
3. Configure dry-run mode for testing stages

## Performance Considerations

- MCP API calls may add latency to contribution generation
- For large numbers of contributions, consider rate limiting
- Repository analysis can be resource-intensive for large codebases

## Security Notes

- API keys are stored in the `.env` file and should be kept secure
- Never commit your `.env` file to version control
- Consider using the built-in credential encryption features

## Further Resources

- [MCP API Documentation](https://mcp.dev/docs/api)
- [GitHub Contribution Hack README](README.md)
- [MCP Dashboard](https://mcp.dev/dashboard) 