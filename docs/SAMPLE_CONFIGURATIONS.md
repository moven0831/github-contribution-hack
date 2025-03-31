# Sample Configurations

This document provides ready-to-use configuration examples for different GitHub contribution patterns. Simply copy the relevant configuration into your `config.yml` file and adjust as needed.

## 1. Consistent Daily Contributor

For users who want to maintain a steady, everyday contribution pattern:

```yaml
# Consistent Daily Contributor
repositories:
  - yourusername/daily-project
  - yourusername/secondary-repo

min_commits: 1
max_commits: 3
min_interval: 20  # hours
max_interval: 24  # hours

# Balanced content generation
mcp_integration:
  enabled: true
  complexity: "medium"
  language_weights:
    python: 0.3
    javascript: 0.3
    markdown: 0.2
    html: 0.1
    css: 0.1
  repository_analysis: true
  content_quality: "high"

# Normal working hours pattern
scheduler:
  working_hours:
    start: 9
    end: 17
  weekend_activity: reduced
```

## 2. Active Open Source Contributor

For simulating an active open source developer pattern:

```yaml
# Active Open Source Contributor
repositories:
  - yourusername/open-source-project1
  - yourusername/open-source-project2
  - yourusername/open-source-project3
  - yourusername/docs-project

min_commits: 3
max_commits: 8
min_interval: 4  # hours
max_interval: 12  # hours

# Varied content with focus on code and documentation
mcp_integration:
  enabled: true
  complexity: "high"
  language_weights:
    python: 0.3
    javascript: 0.2
    typescript: 0.2
    markdown: 0.2
    shell: 0.1
  repository_analysis: true
  content_quality: "high"

# Realistic commit patterns
intelligent_patterns:
  enabled: true
  content_types:
    - code
    - documentation
    - tests
    - configuration
  time_distribution: poisson

# Spread throughout the day with some weekend activity
scheduler:
  working_hours:
    start: 8
    end: 22  # Extended hours typical of OSS contributors
  weekend_activity: normal
```

## 3. Minimal Streak Maintainer

For users who just want to keep their streak alive with minimal activity:

```yaml
# Minimal Streak Maintainer
repositories:
  - yourusername/streak-repo

min_commits: 1
max_commits: 1
min_interval: 22  # hours
max_interval: 24  # hours

# Simple content generation
mcp_integration:
  enabled: false  # Use simpler generation
intelligent_patterns:
  enabled: true
  content_types:
    - documentation
    - text
  time_distribution: random

# Basic commit splitting (avoid empty commits)
split_commits:
  enabled: true
  max_lines_per_commit: 3
  message_prefix: "Update"

# Evening/night activity pattern
scheduler:
  working_hours:
    start: 18
    end: 23
  weekend_activity: normal
```

## 4. Weekend Project Developer

For users who primarily code on weekends:

```yaml
# Weekend Project Developer
repositories:
  - yourusername/weekend-project1
  - yourusername/weekend-project2

min_commits: 5
max_commits: 12
min_interval: 2  # hours
max_interval: 6  # hours

# Focus on weekends with high activity
scheduler:
  weekday_activity: minimal  # Almost no weekday activity
  weekend_activity: high
  weekend_intensity: high
  weekend_hours:
    start: 10
    end: 22

# Varied project content
mcp_integration:
  enabled: true
  complexity: "medium"
  language_weights:
    python: 0.3
    javascript: 0.3
    html: 0.2
    css: 0.2
  content_quality: "high"
```

## 5. Corporate Developer Profile

For simulating a typical corporate developer contribution pattern:

```yaml
# Corporate Developer Profile
repositories:
  - yourusername/work-project1
  - yourusername/work-project2
  - yourusername/documentation

min_commits: 4
max_commits: 10
min_interval: 1  # hours
max_interval: 3  # hours

# Strict working hours, Monday-Friday
scheduler:
  working_hours:
    start: 9   # 9 AM
    end: 17    # 5 PM
  weekend_activity: none
  lunch_break:
    enabled: true
    start: 12
    end: 13
  weekday_only: true

# Enterprise-style content
mcp_integration:
  enabled: true
  complexity: "medium"
  language_weights:
    java: 0.3        # Enterprise languages
    csharp: 0.2
    typescript: 0.2
    sql: 0.1
    markdown: 0.2
  repository_analysis: true
  content_quality: "high"
```

## 6. Academic/Research Profile

For students and researchers:

```yaml
# Academic/Research Profile
repositories:
  - yourusername/research-project
  - yourusername/thesis-code
  - yourusername/data-analysis

min_commits: 2
max_commits: 5
min_interval: 8  # hours
max_interval: 16  # hours

# Focus on data analysis and documentation
mcp_integration:
  enabled: true
  complexity: "high"
  language_weights:
    python: 0.5    # Data science focus
    r: 0.2
    jupyter: 0.2
    markdown: 0.1
  content_quality: "high"

# Academic schedule with semester pattern
scheduler:
  working_hours:
    start: 10  # Later start
    end: 20    # Later end
  weekend_activity: reduced
  seasonal_intensity:
    enabled: true
    high_seasons: ["January-May", "September-December"]  # Semesters
    low_seasons: ["June-August", "December 15-January 5"]  # Breaks
```

## 7. Professional Portfolio Showcase

For job seekers wanting to showcase professional-level activity:

```yaml
# Professional Portfolio Showcase
repositories:
  - yourusername/showcase-project1
  - yourusername/showcase-project2
  - yourusername/blog
  - yourusername/portfolio-site

min_commits: 4
max_commits: 8
min_interval: 6  # hours
max_interval: 12  # hours

# High-quality, diverse content
mcp_integration:
  enabled: true
  complexity: "high"
  language_weights:
    python: 0.2
    javascript: 0.2
    typescript: 0.1
    react: 0.1
    vue: 0.1
    node: 0.1
    markdown: 0.1
    html: 0.05
    css: 0.05
  repository_analysis: true
  content_quality: "high"

# Project-focused commit messages
intelligent_patterns:
  enabled: true
  content_types:
    - feature
    - bugfix
    - refactor
    - docs
    - tests
  commit_message_quality: "high"

# Consistent, professional schedule
scheduler:
  working_hours:
    start: 8
    end: 18
  weekend_activity: moderate
```

## 8. Startup Founder Pattern

For those simulating the irregular but intense activity of startup work:

```yaml
# Startup Founder Pattern
repositories:
  - yourusername/startup-project
  - yourusername/mvp-code
  - yourusername/landing-page

min_commits: 3
max_commits: 15  # Wide range, some days very intense
min_interval: 1   # hours
max_interval: 12  # hours

# Irregular but intense schedule
scheduler:
  irregular_pattern: true
  sprint_cycles:
    enabled: true
    sprint_length_days: 7
    cooldown_days: 2
  all_hours: true  # Activity can happen any time

# Startup-focused tech stack
mcp_integration:
  enabled: true
  complexity: "high"
  language_weights:
    javascript: 0.3
    typescript: 0.2
    python: 0.2
    react: 0.1
    node: 0.1
    html: 0.05
    css: 0.05
  content_quality: "high"
```

## 9. Seasonal Contributor

For users with seasonal coding patterns:

```yaml
# Seasonal Contributor
repositories:
  - yourusername/seasonal-project
  - yourusername/occasional-updates

min_commits: 0  # Can have days with no commits
max_commits: 5
min_interval: 24  # hours
max_interval: 72  # hours

# Seasonal pattern with bursts of activity
scheduler:
  seasonal_pattern: true
  active_months: ["January", "February", "October", "November", "December"]
  reduced_months: ["March", "April", "September"]
  inactive_months: ["May", "June", "July", "August"]
  
  active_settings:
    min_commits: 2
    max_commits: 5
  reduced_settings:
    min_commits: 1
    max_commits: 2
  inactive_settings:
    min_commits: 0
    max_commits: 1
    probability: 0.3  # 30% chance of commit on inactive days
```

## 10. Mixed Activity Pattern

For users with multiple projects and varied activity:

```yaml
# Mixed Activity Pattern
repositories:
  - yourusername/main-project
  - yourusername/side-project
  - yourusername/blog-content
  - yourusername/learning-repo

# Allow repositories to have different settings
repository_specific:
  - name: yourusername/main-project
    min_commits: 2
    max_commits: 5
    content:
      mcp_complexity: "high"
      languages: ["typescript", "react", "node"]
  
  - name: yourusername/side-project
    min_commits: 0
    max_commits: 3
    schedule:
      weekend_only: true
    content:
      mcp_complexity: "medium"
      languages: ["python", "django"]
  
  - name: yourusername/blog-content
    min_commits: 0
    max_commits: 1
    schedule:
      days: ["Monday", "Thursday"]
    content:
      mcp_complexity: "medium"
      languages: ["markdown"]
  
  - name: yourusername/learning-repo
    min_commits: 0
    max_commits: 2
    schedule:
      probability: 0.4  # 40% chance of commit
    content:
      mcp_complexity: "low"
      languages: ["python", "javascript"]

# Global settings (apply when not overridden by repository-specific settings)
min_commits: 1
max_commits: 3
min_interval: 12  # hours
max_interval: 24  # hours

mcp_integration:
  enabled: true
  complexity: "medium"  # Default complexity
  content_quality: "high"
```

## Combining Configurations

You can combine elements from different configurations to create your ideal pattern. For example:

```yaml
# Custom Combined Configuration

# Repositories
repositories:
  - yourusername/main-repo
  - yourusername/side-project
  - yourusername/documentation

# Basic settings
min_commits: 2
max_commits: 6
min_interval: 6  # hours
max_interval: 18  # hours

# MCP integration from "Professional Portfolio Showcase"
mcp_integration:
  enabled: true
  complexity: "high"
  language_weights:
    python: 0.3
    javascript: 0.3
    typescript: 0.1
    markdown: 0.2
    html: 0.05
    css: 0.05
  repository_analysis: true
  content_quality: "high"

# Scheduling from "Corporate Developer Profile"
scheduler:
  working_hours:
    start: 9   # 9 AM
    end: 17    # 5 PM
  weekend_activity: reduced
  lunch_break:
    enabled: true
    start: 12
    end: 13

# Intelligent patterns from "Active Open Source Contributor"
intelligent_patterns:
  enabled: true
  content_types:
    - code
    - documentation
    - tests
    - configuration
  time_distribution: poisson
```

Remember to adjust these sample configurations to match your specific needs and repositories. These are starting points that you can customize further based on your desired contribution pattern. 