"""
Visualization module for GitHub Contribution Patterns

Provides tools for visualizing contribution patterns, 
including heatmaps, streak analysis, and activity timelines.
"""
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import calendar
import tempfile
import os
from pathlib import Path
import io
import base64
from typing import Dict, List, Tuple, Optional, Union

class ContributionVisualizer:
    def __init__(self, db_path='contributions.db'):
        """
        Initialize the contribution visualizer
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self._check_database()
        
        # Set default styles for consistent visuals
        plt.style.use('ggplot')
        
        # Create cache directory for exports
        self.cache_dir = Path(tempfile.gettempdir()) / 'github_contrib_viz'
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _check_database(self):
        """Check if the database exists and has the expected schema"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if contributions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contributions'")
            if not cursor.fetchone():
                raise ValueError("Database does not contain the contributions table")
                
            conn.close()
        except sqlite3.Error as e:
            raise ValueError(f"Database error: {str(e)}")

    def _get_contribution_data(self, days=365) -> Tuple[List[datetime], List[int]]:
        """
        Get contribution data for the specified period
        
        Args:
            days: Number of days to include
            
        Returns:
            Tuple of (dates, counts)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate start date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query contributions by day
            cursor.execute('''
                SELECT DATE(timestamp), SUM(commit_count)
                FROM contributions
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            ''', (start_date.isoformat(),))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return [], []
                
            dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in results]
            counts = [int(row[1]) for row in results]
            
            return dates, counts
            
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return [], []

    def generate_heatmap(self, days=365, save_path=None) -> Optional[str]:
        """
        Generate a GitHub-style contribution heatmap
        
        Args:
            days: Number of days to include
            save_path: Path to save the image (optional)
            
        Returns:
            Path to the generated image or None if error
        """
        dates, counts = self._get_contribution_data(days)
        
        if not dates:
            return None
            
        # Fill in missing dates with zero commits
        all_dates = []
        all_counts = []
        
        current_date = min(dates)
        end_date = max(dates)
        
        while current_date <= end_date:
            if current_date in dates:
                idx = dates.index(current_date)
                all_counts.append(counts[idx])
            else:
                all_counts.append(0)
                
            all_dates.append(current_date)
            current_date += timedelta(days=1)
            
        # Calculate number of weeks and create matrix
        num_weeks = len(all_dates) // 7 + (1 if len(all_dates) % 7 > 0 else 0)
        activity_matrix = np.zeros((7, num_weeks))
        
        # Fill matrix with commit counts
        for i, (date, count) in enumerate(zip(all_dates, all_counts)):
            weekday = date.weekday()
            week = i // 7
            if week < num_weeks:
                activity_matrix[weekday, week] = count
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 4))
        
        # Color mapping similar to GitHub's
        cmap = plt.cm.Greens
        
        # Plot heatmap
        heatmap = ax.pcolor(activity_matrix, cmap=cmap, edgecolors='white', linewidths=1)
        
        # Set y-axis labels (weekdays)
        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        ax.set_yticks(np.arange(7) + 0.5)
        ax.set_yticklabels(weekdays)
        
        # Create month labels for x-axis
        month_labels = []
        month_positions = []
        
        current_month = None
        for i, date in enumerate(all_dates):
            if date.month != current_month:
                current_month = date.month
                month_labels.append(calendar.month_abbr[current_month])
                month_positions.append(i // 7)
        
        ax.set_xticks(month_positions)
        ax.set_xticklabels(month_labels)
        
        # Add title
        ax.set_title('Contribution Activity Heatmap')
        
        # Add colorbar
        cbar = plt.colorbar(heatmap, ax=ax)
        cbar.set_label('Contributions')
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return save_path
        else:
            # Generate a temporary file
            temp_file = self.cache_dir / f"heatmap_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            plt.savefig(temp_file, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return str(temp_file)

    def generate_streak_chart(self, save_path=None) -> Optional[str]:
        """
        Generate a streak analysis chart
        
        Args:
            save_path: Path to save the image (optional)
            
        Returns:
            Path to the generated image or None if error
        """
        dates, counts = self._get_contribution_data(365)
        
        if not dates:
            return None
            
        # Fill in missing dates with zero commits
        all_dates = []
        all_counts = []
        
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if current_date in dates:
                idx = dates.index(current_date)
                all_counts.append(counts[idx])
            else:
                all_counts.append(0)
                
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        streaks = []
        
        for count in reversed(all_counts):  # Start from most recent
            if count > 0:
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0
            
            longest_streak = max(longest_streak, current_streak)
        
        if current_streak > 0:
            streaks.append(current_streak)
        
        # Create the streak chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot streak distribution as a histogram
        if streaks:
            ax.hist(streaks, bins=range(1, max(streaks) + 2), alpha=0.7, color='skyblue', edgecolor='black')
            
            # Add current streak line
            if current_streak > 0:
                ax.axvline(x=current_streak, color='red', linestyle='--', linewidth=2, 
                           label=f'Current Streak: {current_streak} days')
            
            # Add longest streak line
            ax.axvline(x=longest_streak, color='green', linestyle='-', linewidth=2,
                       label=f'Longest Streak: {longest_streak} days')
            
            ax.legend()
            
        ax.set_title('Contribution Streak Analysis')
        ax.set_xlabel('Streak Length (days)')
        ax.set_ylabel('Frequency')
        
        # Set x-axis to integers only
        ax.set_xticks(range(0, max(streaks) + 2 if streaks else 2))
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return save_path
        else:
            # Generate a temporary file
            temp_file = self.cache_dir / f"streak_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            plt.savefig(temp_file, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return str(temp_file)

    def generate_activity_timeline(self, days=90, save_path=None) -> Optional[str]:
        """
        Generate an activity timeline
        
        Args:
            days: Number of days to include
            save_path: Path to save the image (optional)
            
        Returns:
            Path to the generated image or None if error
        """
        dates, counts = self._get_contribution_data(days)
        
        if not dates:
            return None
            
        # Create the activity timeline
        fig, ax = plt.subplots(figsize=(12, 5))
        
        # Plot activity as a line chart
        ax.plot(dates, counts, marker='o', linestyle='-', linewidth=2, markersize=5)
        
        # Add moving average
        window = min(7, len(counts))
        if window > 0:
            moving_avg = np.convolve(counts, np.ones(window) / window, mode='valid')
            moving_avg_dates = dates[window-1:]
            ax.plot(moving_avg_dates, moving_avg, linestyle='--', color='red', 
                    linewidth=2, label=f'{window}-day Moving Average')
        
        ax.set_title('Contribution Activity Timeline')
        ax.set_xlabel('Date')
        ax.set_ylabel('Contributions')
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend
        ax.legend()
        
        # Save the figure if requested
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return save_path
        else:
            # Generate a temporary file
            temp_file = self.cache_dir / f"timeline_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            plt.savefig(temp_file, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return str(temp_file)

    def generate_repo_distribution(self, save_path=None) -> Optional[str]:
        """
        Generate a repository distribution chart
        
        Args:
            save_path: Path to save the image (optional)
            
        Returns:
            Path to the generated image or None if error
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query contributions by repository
            cursor.execute('''
                SELECT repo, SUM(commit_count)
                FROM contributions
                GROUP BY repo
                ORDER BY SUM(commit_count) DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return None
                
            repos = [row[0] for row in results]
            counts = [int(row[1]) for row in results]
            
            # Limit to top 10 repositories
            if len(repos) > 10:
                other_count = sum(counts[10:])
                repos = repos[:10] + ['Other']
                counts = counts[:10] + [other_count]
                
            # Create the pie chart
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Plot pie chart
            wedges, texts, autotexts = ax.pie(
                counts, 
                labels=repos,
                autopct='%1.1f%%',
                shadow=True,
                startangle=90,
                textprops={'fontsize': 9}
            )
            
            # Ensure the pie is a circle
            ax.axis('equal')
            
            ax.set_title('Repository Distribution')
            
            # Save the figure if requested
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                plt.close(fig)
                return save_path
            else:
                # Generate a temporary file
                temp_file = self.cache_dir / f"repos_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                plt.savefig(temp_file, dpi=150, bbox_inches='tight')
                plt.close(fig)
                return str(temp_file)
                
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return None

    def get_image_base64(self, image_path) -> Optional[str]:
        """
        Convert an image to base64 for embedding in HTML
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image or None if error
        """
        try:
            with open(image_path, 'rb') as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {str(e)}")
            return None

def main():
    """Main function for testing the visualizer"""
    visualizer = ContributionVisualizer()
    
    # Generate sample visualizations
    heatmap_path = visualizer.generate_heatmap()
    streak_path = visualizer.generate_streak_chart()
    timeline_path = visualizer.generate_activity_timeline()
    repo_path = visualizer.generate_repo_distribution()
    
    print(f"Generated heatmap: {heatmap_path}")
    print(f"Generated streak chart: {streak_path}")
    print(f"Generated timeline: {timeline_path}")
    print(f"Generated repo distribution: {repo_path}")

if __name__ == "__main__":
    main() 