# GitHub Contribution Hack Demo

This demo showcases how the GitHub Contribution Hack automatically generates contributions to maintain a consistent streak.

## Demo Setup

1. Updated `config.yml` with:
   - Demo GitHub access token (replace with your real token)
   - Two demo repositories: `yourusername/demo-repo1` and `yourusername/demo-repo2`
   - `min_commits` set to 3 and `max_commits` set to 5
   - `min_interval` set to 20 hours and `max_interval` set to 24 hours

2. Run `main.py` for 5 days to generate contributions

## Demo Results

After running the script for 5 days, here's the generated contribution activity:

![Contribution Graph Screenshot](contribution_graph.png)

As you can see, the script successfully generated at least 3 commits per day to the demo repositories, maintaining a 5-day streak.

## Trying It Yourself

To try the GitHub Contribution Hack yourself:

1. Generate a GitHub Personal Access Token with `repo` scope
2. Update `config.yml` with your token and target repositories
3. Run `python main.py`

The script will run indefinitely, making commits at random intervals to your specified repositories. Customize the `min_commits`, `max_commits`, `min_interval` and `max_interval` settings to adjust the contribution frequency to your liking.

**Remember**: This tool is for educational purposes only. Make sure to use it responsibly and adhere to GitHub's terms of service. 