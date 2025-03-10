class ContributionAnalytics:
    def __init__(self):
        self._init_database()
        self._setup_visualization()
        
    def _init_database(self):
        """Initialize SQLite database for tracking"""
        import sqlite3
        self.conn = sqlite3.connect('contributions.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS contributions
                             (timestamp DATETIME, repo TEXT, 
                             commit_count INTEGER, lines_changed INTEGER,
                             file_type TEXT)''')

    def _setup_visualization(self):
        """Setup visualization components"""
        try:
            from rich.console import Console
            from rich.panel import Panel
            self.console = Console()
        except ImportError:
            # Fallback if rich is not available
            self.console = None
            print("Warning: Rich library not available, visualization will be limited")

    def log_contribution(self, repo, commit_count, lines_changed, file_type):
        """Log contribution details to database"""
        self.cursor.execute('''INSERT INTO contributions VALUES 
                            (datetime('now'), ?, ?, ?, ?)''',
                            (repo, commit_count, lines_changed, file_type))
        self.conn.commit()

    def generate_report(self):
        """Generate analytics report"""
        report = {
            'current_streak': self._calculate_streak(),
            'daily_average': self._daily_average(),
            'success_probability': self._success_probability(),
            'repo_activity': self._repo_activity_distribution()
        }
        self._display_dashboard(report)
        return report

    def _calculate_streak(self):
        """Calculate current contribution streak"""
        self.cursor.execute('''SELECT DISTINCT DATE(timestamp) 
                            FROM contributions ORDER BY timestamp DESC''')
        dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in self.cursor.fetchall()]
        return self._consecutive_days(dates)

    def _success_probability(self):
        """Predict streak success probability using historical data"""
        from sklearn.linear_model import LinearRegression
        self.cursor.execute('''SELECT COUNT(*) FROM contributions 
                            GROUP BY DATE(timestamp)''')
        daily_counts = [row[0] for row in self.cursor.fetchall()]
        
        if len(daily_counts) < 2:
            return 0.7  # Default confidence
            
        X = [[i] for i in range(len(daily_counts))]
        y = daily_counts
        model = LinearRegression().fit(X, y)
        return max(0, min(1, model.coef_[0] * 0.1 + 0.5))

    def _display_dashboard(self, report):
        """Display terminal dashboard"""
        from rich.console import Console
        from rich.table import Table
        from rich.live import Live
        from rich.layout import Layout

        console = Console()
        layout = Layout()

        # Create header
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=2),
            Layout(name="stats", size=8)
        )

        # Header panel
        layout["header"].update(
            Panel(f"[bold]GitHub Contribution Analytics[/] | Streak: {report['current_streak']} days")
        )

        # Main chart
        dates, counts = self._get_weekly_data()
        chart = BarChart(width=60)
        for date, count in zip(dates, counts):
            chart.add(date, count)
        layout["main"].update(chart)

        # Stats table
        table = Table(show_header=False)
        table.add_row("Daily Average", f"{report['daily_average']:.1f}")
        table.add_row("Success Probability", f"{report['success_probability']*100:.1f}%")
        table.add_row("Active Repos", ", ".join(report['repo_activity'].keys()))
        layout["stats"].update(table)

        with Live(layout, refresh_per_second=4):
            time.sleep(0.5) 