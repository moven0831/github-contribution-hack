# GitHub Contribution Hack Demo

This demo showcases how the GitHub Contribution Hack automatically generates contributions to maintain a consistent streak.

## Demo Setup

1. Install the required Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Update the `config.yml` file with your settings:
   - Add your GitHub access token (generate one with `repo` scope) 
   - Specify the repositories you want to contribute to in the `repositories` list
   - Adjust `min_commits` and `max_commits` to set the number of commits made per run
   - Set `min_interval` and `max_interval` (in hours) to control the time between runs
   - Optionally enable the `split_commits` feature to split large commits into smaller ones:
     - Set `enabled` to `true` 
     - Specify the `max_lines_per_commit` to control the size of each split commit
     - Provide a `message_prefix` that will be included in each split commit message

   Example `config.yml`:
   ```yaml
   github_token: your_github_token_here
   repositories:
     - yourusername/repo1 
     - yourusername/repo2
   min_commits: 3
   max_commits: 5
   min_interval: 20 
   max_interval: 24
   split_commits:
     enabled: true
     max_lines_per_commit: 10
     message_prefix: "Split commit"
   ```

3. Run the `main.py` script:
   ```
   python main.py
   ```
   
   The script will run indefinitely, making automated commits to your specified repositories at random intervals between `min_interval` and `max_interval` hours. Each run will generate between `min_commits` and `max_commits` commits.

   The script clones your repositories to a local `repos/` directory, makes the commits there, and pushes the changes to GitHub.

4. Let it run for a few days and then check your contribution graph on GitHub to see the generated activity! The longer you let it run, the more impressive the streak will look.

Remember, this is just a demo for educational purposes. Make sure to use it responsibly and don't violate GitHub's terms of service. Have fun hacking your contributions!

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