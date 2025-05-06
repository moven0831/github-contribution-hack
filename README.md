# Stay in a Streak! GitHub Contribution Hack

This project provides a tool to automatically make contributions to a connected GitHub account, helping you maintain a consistent activity streak on your contribution graph.

## Features

- Automatically create commits and push them to GitHub on a regular schedule
- Configurable settings for commit frequency and repository selection
- Seamless integration with GitHub API for authentication and contribution tracking
- **Centralized Configuration**: Easy management of all settings via `config.yml` using the new `ConfigManager`.
- **Enhanced Security**: Encrypted credential storage and system keyring integration
- **Intelligent Patterns**: ML-powered commit messages and natural time distribution
- **Real-Time Monitoring**: Interactive dashboard with streak analytics and verification
- **MCP Integration**: AI-powered code and commit generation for more realistic contributions
- Cross-platform compatibility (Windows, macOS, Linux)
- **Enhanced User Experience**: Interactive CLI, web interface, visualizations, and notifications

## Documentation

- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Error Handling Guide](docs/ERROR_HANDLING.md) - Error handling documentation
- [MCP Integration](MCP_INTEGRATION.md) - Guide for AI-powered content generation
- [Demo Guide](DEMO.md) - Quick start demonstration
- [Use Cases](docs/USE_CASES.md) - Comprehensive examples for various scenarios
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Solutions for common issues
- [Sample Configurations](docs/SAMPLE_CONFIGURATIONS.md) - Ready-to-use configuration examples
- [Best Practices](docs/BEST_PRACTICES.md) - Guidelines for responsible usage
- [Contributing](CONTRIBUTING.md) - Guide for contributors

## Configuration (`config.yml`)

This project now uses a centralized `config.yml` file to manage all its settings. A `ConfigManager` class (`config_loader.py`) is responsible for loading, accessing, and saving this configuration, ensuring a single source of truth for all modules.

Below are the key configuration sections and options available. For sensitive information like API keys (`GITHUB_TOKEN`, `MCP_API_KEY`), it's recommended to use environment variables, which are typically loaded by the application and can override or supplement values from `config.yml`.

### Core Settings

-   `repositories`: List of repository names (e.g., `username/repo-name`) to make contributions to.
-   `min_commits`: Minimum number of commits per repository per run (Default: `1`).
-   `max_commits`: Maximum number of commits per repository per run (Default: `3`).
-   `min_interval`: Minimum interval between contribution runs in hours (Default: `12`).
-   `max_interval`: Maximum interval between contribution runs in hours (Default: `24`).

### Database

-   `database`:
    -   `path`: Path to the SQLite database file (Default: `"contributions.db"`). Used by analytics and visualization.

### Performance

-   `performance`:
    -   `max_workers`: Maximum number of concurrent threads for processing repositories (Default: `4`).
    -   `parallel_repos`: Boolean, whether to process repositories in parallel (Default: `True`).

### Commit Generation (General)

These settings apply when MCP is disabled or if it fails.

-   `commit_generation`:
    -   `ml_based_chance`: Probability (0.0 to 1.0) of using the Markovify model for commit messages (Default: `0.3`).
    -   `code_content_chance`: Probability (0.0 to 1.0) of generating code-like content versus documentation-like content (Default: `0.4`).
    -   `file_types`: List of file extensions to use for generated files (Default: `["txt", "md", "py", "js", "json"]`).

### Split Commits

-   `split_commits`:
    -   `enabled`: Boolean, whether to split large generated content into multiple smaller commits (Default: `true`).
    -   `max_lines_per_commit`: Maximum lines of content per split commit (Default: `5`).
    -   `message_prefix`: Prefix for commit messages of split commits (Default: `"Automated commit"`).

### MCP Integration (AI-Powered Content)

-   `mcp_integration`:
    -   `enabled`: Boolean, set to `true` to enable AI-powered content generation (Default: `false`).
    -   `api_key`: Your MCP API key. Can also be set via `MCP_API_KEY` environment variable. (Default: `null`).
    -   `api_endpoint`: The API endpoint for MCP (Default: `"https://api.mcp.dev/v1"`).
    -   `max_retries`: Maximum number of retries for MCP API calls (Default: `3`).
    -   `request_timeout`: Timeout in seconds for MCP API requests (Default: `15`).
    -   `complexity`: Desired complexity of generated content (`"low"`, `"medium"`, `"high"`) (Default: `"low"`).
    -   `language_weights`: A dictionary defining the probability for generating content in specific languages (e.g., `python: 0.4`, `javascript: 0.3`).
    -   `repository_analysis`: Boolean, allow MCP to analyze repository context (Default: `true`).
    -   `content_quality`: Desired quality of content (e.g., `"medium"`) (Default: `"medium"`).
    -   `dry_run`: Boolean, if `true`, MCP calls are simulated (Default: `false`).

### Visualization

-   `visualization`:
    -   `style`: Default Matplotlib style for charts (e.g., `"ggplot"`, `"seaborn-v0_8-darkgrid"`) (Default: `"ggplot"`).
    -   `cache_dir`: Base directory for caching visualization images. Set to `null` for system temp directory (e.g., `".cache/viz_output"` or `/tmp/github_contrib_viz`) (Default: `null`).
    -   `heatmap`:
        -   `days`: Number of days to include in the heatmap (Default: `365`).
        -   `color_scheme`: Matplotlib Cmap for heatmap (e.g., `"Greens"`, `"YlGn"`) (Default: `"Greens"`).
    -   `activity_timeline`:
        -   `days`: Number of days for the activity timeline (Default: `90`).
    -   `repo_distribution`:
        -   `limit_repos`: Max repositories in pie chart before grouping into "Other" (Default: `10`).

### Notifications

-   `notifications`:
    -   `enabled`: Boolean, master switch for all notifications (Default: `true`).
    -   `manager`: Settings for the `NotificationManager`.
        -   `max_history`: Max number of notifications to keep in history (Default: `100`).
        -   `level_routing`: Default channels for notifications by level (e.g., `info: ["desktop"]`, `error: ["email", "webhook"]`).
        -   `throttle_rules`: Dictionary of rules to prevent notification spam. Each rule has a `pattern` (regex for title), `max_count`, and `time_window_seconds`.
            -   Example rule: `frequent_info: { pattern: ".*Info Notification.*", max_count: 10, time_window_seconds: 1800 }`
    -   `email`:
        -   `enabled`: Boolean, enable email notifications (Default: `false`).
        -   `smtp_server`, `smtp_port`, `username`, `password`, `sender`, `recipients`: Standard email settings.
    -   `webhook`:
        -   `enabled`: Boolean, enable webhook notifications (Default: `false`).
        -   `url`: URL for the webhook endpoint.
        -   `custom_headers`: Optional custom HTTP headers.
    -   `desktop`:
        -   `enabled`: Boolean, enable desktop notifications (requires `notify2` or `plyer` package) (Default: `true`).

### Other Sections

The `config.yml` may also contain other sections like `intelligent_patterns`, `monitoring`, `analytics`, and `ui`. These are generally used by specific modules or older parts of the application. Refer to the comments within `config.yml` for their specific purposes.

## Getting Started

### Prerequisites

- Python 3.x installed
- GitHub account with personal access token
- Git installed on your system
- [Optional] Node.js v18+ for advanced monitoring features
- [Optional] MCP API key for enhanced code generation

### Security Setup (Non-Docker)

*Note: This setup is for running the application directly on your machine. For Docker setups, configure credentials using the `.env` file as described in the Docker section.*

Instead of manual .env configuration, run the security initialization:
```bash
python setup_security.py
```
This will guide you through:
1. Encrypting your GitHub token
2. Setting up system keyring integration
3. Configuring automatic credential rotation

### Intelligent Commit Configuration

Enable smart patterns in `config.yml`:
```yaml
intelligent_patterns:
  enabled: true
  content_types: [code, docs, config]
  time_distribution: poisson
```

### MCP Integration Setup

For enhanced AI-powered code and commit generation:

1. Obtain an MCP API key from the MCP dashboard
2. Add your API key to the `.env` file:
   ```
   MCP_API_KEY=your_mcp_api_key_here
   ```
3. Enable MCP integration in `config.yml`:
   ```yaml
   mcp_integration:
     enabled: true
     complexity: "medium"  # low, medium, high
   ```

For full MCP integration documentation, see [MCP_INTEGRATION.md](MCP_INTEGRATION.md).

### User Experience Features

#### Interactive CLI

Start the interactive command-line interface:
```bash
python main.py --interactive
```

The CLI provides:
- Real-time status updates
- Progress indicators for contribution processes
- Service health monitoring
- Contribution analytics dashboard

#### Web Interface

Start the web-based dashboard:
```bash
python main.py --web
# Optionally specify host and port
python main.py --web --host 0.0.0.0 --port 8080
```

Features of the web interface:
- Dashboard with contribution statistics
- Visualization of contribution patterns
- Configuration management
- Notification history and testing

#### Visualization Tools

Generate visualizations of your contribution patterns:
```bash
# Generate all visualizations
python main.py --visualize all

# Generate specific visualizations
python main.py --visualize heatmap
python main.py --visualize streak
python main.py --visualize timeline
python main.py --visualize repo
```

Available visualizations:
- Contribution heatmap (GitHub-style calendar view)
- Streak analysis (current and longest streaks)
- Activity timeline (contributions over time)
- Repository distribution (pie chart of activity by repository)

#### Notification System

Configure notifications in `config.yml` as described in the **Configuration (`config.yml`)** section above.
The system supports various channels and fine-grained control over routing and throttling.

### Monitoring Dashboard

Start the interactive analytics dashboard:
```bash
python main.py --monitor
```

Key monitoring features:
- Real-time contribution graph
- Streak success probability estimation
- Repository activity distribution
- Automated GitHub commit verification

## Running with Docker (Recommended)

Using Docker and Docker Compose is the recommended way to run this application, as it encapsulates dependencies and ensures a consistent runtime environment across different machines.

### Prerequisites

-   [Docker](https://docs.docker.com/get-docker/) installed
-   [Docker Compose](https://docs.docker.com/compose/install/) installed (usually included with Docker Desktop)

### Configuration

1.  **Copy the example environment file:**
    ```bash
    cp .env.example .env
    ```
2.  **Edit the `.env` file:** Add your GitHub Personal Access Token:
    ```env
    GITHUB_TOKEN=your_github_token_here
    # Add other variables like MCP_API_KEY if needed
    ```
    *Note: For Docker setups, credentials are provided via this `.env` file. The `setup_security.py` script is intended for non-Docker environments.*

### Usage

1.  **Build and Run (Default - Contribution Logic):**
    To build the Docker image and start the container running the main contribution script (`main.py`):
    ```bash
    docker-compose up --build
    ```
    The `--build` flag is only needed the first time or when you change `Dockerfile` or `requirements.txt`. Use `docker-compose up` for subsequent runs. To run in the background, use `docker-compose up -d`.

2.  **Run the Web Interface:**
    To start the web interface instead of the default script:
    ```bash
    docker-compose run --rm --service-ports app python main.py --web --host 0.0.0.0
    ```
    -   `--rm`: Automatically removes the container when it exits.
    -   `--service-ports`: Publishes the port defined in `docker-compose.yml` (5000).
    -   `app`: The name of the service defined in `docker-compose.yml`.
    -   `python main.py --web --host 0.0.0.0`: The command to run inside the container.

3.  **Stop the Application:**
    To stop the services started with `docker-compose up`:
    ```bash
    docker-compose down
    ```
    If you ran in detached mode (`-d`), this command is necessary to stop the containers. It stops and removes the containers and the network created by Compose.

### Development with Docker

The `docker-compose.yml` file includes a commented-out `volumes` section. If you uncomment the `- .:/app` line, the project directory on your host machine will be mounted into the container at `/app`. This means code changes you make locally will be reflected inside the container immediately, which is useful for development without needing to rebuild the image constantly.

## Development and Testing

### Running Tests

The project includes comprehensive unit tests for all functionality including MCP integration:

```bash
# Install testing dependencies
pip install -r requirements.txt

# Run all tests with coverage report
python run_tests.py

# Run specific test files
pytest tests/test_mcp_integration.py
```

Test coverage reports are generated in the `coverage_html` directory.

### Test Structure

- `tests/test_mcp_integration.py`: Tests for the MCP client functionality
- `tests/test_main_mcp.py`: Tests for integration with the main script
- `tests/test_config_loader.py`: Tests for the ConfigManager (NEW)

For more details on testing, see [tests/README.md](tests/README.md).

## Advanced Features

### Security Recommendations
```bash
# Rotate credentials monthly
python setup_security.py --rotate

# Audit stored credentials
python setup_security.py --audit
```

### Pattern Customization
1. Collect historical commits in commit_patterns.json
2. Retrain the ML model:
```bash
python train_patterns.py --input commit_patterns.json
```

### MCP Content Customization
Adjust language distribution and code complexity:
```yaml
mcp_integration:
  language_weights:
    python: 0.6    # More Python code
    javascript: 0.2
    markdown: 0.2
  complexity: "high"  # Generate more sophisticated code
```

### Analytics Integration
View historical reports:
```bash
python analytics.py --report weekly-summary
```

Export monitoring data:
```bash
python analytics.py --export csv
```

Note: The monitoring dashboard requires additional dependencies:
```bash
pip install -r requirements-monitoring.txt
```

### Quick Start Demo

To quickly see the GitHub Contribution Hack in action:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/github-contribution-hack.git
   cd github-contribution-hack
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your GitHub token:
   - Generate a GitHub Personal Access Token with `repo` scope at https://github.com/settings/tokens
   - Copy the `.env.example` file to `.env`:
     ```
     cp .env.example .env
     ```
   - Replace `your_github_token_here` in `.env` with your actual token

## Deploying with Docker

You can build and run this application using Docker for easy deployment on cloud servers or any machine with Docker installed.

### Prerequisites

- Docker installed on your system.

### Building the Docker Image

Navigate to the project's root directory (where the `Dockerfile` is located) and run the following command to build the image. Replace `<image_name>` with a name for your image (e.g., `github-contributor`).

```bash
docker build -t <image_name> .
```

### Running the Container

#### Standard Contribution Mode

To run the container in the default mode (which executes `hack.make_contributions()`):

```bash
docker run --rm -e GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN" <image_name>
```

**Important:** You MUST provide your GitHub Personal Access Token via the `GITHUB_TOKEN` environment variable.

#### Web Interface Mode

To run the container with the web interface enabled:

```bash
docker run --rm -e GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN" -p 5000:5000 <image_name> python main.py --web --host 0.0.0.0 --port 5000
```

This will:
- Pass your GitHub token.
- Map port 5000 on your host machine to port 5000 in the container.
- Start the web interface listening on all interfaces (`0.0.0.0`) inside the container.
- You can then access the web interface at `http://localhost:5000` (or your server's IP address if running remotely).

#### Using a Custom Configuration

If you want to use a `config.yml` file from your host machine instead of the one included in the image, you can mount it as a volume:

```bash
# Example for standard mode with custom config
docker run --rm \\
  -e GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN" \\
  -v $(pwd)/path/to/your/config.yml:/app/config.yml \\
  <image_name>

# Example for web mode with custom config
docker run --rm \\
  -e GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN" \\
  -p 5000:5000 \\
  -v $(pwd)/path/to/your/config.yml:/app/config.yml \\
  <image_name> python main.py --web --host 0.0.0.0 --port 5000
```

Replace `$(pwd)/path/to/your/config.yml` with the actual path to your configuration file.

## Responsible Usage

Please use this tool responsibly and ethically. See our [Best Practices](docs/BEST_PRACTICES.md) guide for guidelines on responsible usage.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
