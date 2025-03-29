"""
Interactive CLI Interface for GitHub Contribution Hack

Provides a rich terminal interface with progress indicators, 
status updates, and interactive controls.
"""
import time
import threading
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich import box

class InteractiveCLI:
    def __init__(self, analytics=None, health_monitor=None):
        """
        Initialize the interactive CLI interface
        
        Args:
            analytics: ContributionAnalytics instance
            health_monitor: ServiceMonitor instance
        """
        self.console = Console()
        self.analytics = analytics
        self.health_monitor = health_monitor
        self.running = False
        self.live = None
        self.layout = Layout()
        self._setup_layout()
        
    def _setup_layout(self):
        """Setup the layout for the CLI interface"""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        self.layout["body"].split_row(
            Layout(name="main", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        
        self.layout["main"].split(
            Layout(name="status", size=3),
            Layout(name="content")
        )
        
        self.layout["sidebar"].split(
            Layout(name="health", ratio=1),
            Layout(name="stats", ratio=1)
        )
        
        self.layout["header"].update(
            Panel(
                "[bold cyan]GitHub Contribution Hack[/] [green]Interactive CLI[/]",
                border_style="bright_blue"
            )
        )
    
    def start(self):
        """Start the interactive CLI interface"""
        self.running = True
        with Live(self.layout, refresh_per_second=4, screen=True) as self.live:
            try:
                self._update_loop()
            except KeyboardInterrupt:
                self.stop()
    
    def stop(self):
        """Stop the interactive CLI interface"""
        self.running = False
        if self.live:
            self.live.stop()
    
    def _update_loop(self):
        """Main update loop for the UI"""
        while self.running:
            self._update_status()
            self._update_health()
            self._update_stats()
            self._update_content()
            time.sleep(0.5)
    
    def _update_status(self):
        """Update the status section"""
        if self.health_monitor:
            overall = self.health_monitor.get_overall_system_status()
            color = {
                "ok": "green",
                "warning": "yellow",
                "error": "red",
                "unknown": "grey"
            }.get(overall.get("status", "unknown"), "white")
            
            self.layout["status"].update(
                Panel(
                    f"[bold {color}]System Status: {overall.get('status', 'Unknown').upper()}[/] | {overall.get('message', '')}",
                    border_style=color
                )
            )
        else:
            self.layout["status"].update(
                Panel("System Status: Not Available", border_style="yellow")
            )
    
    def _update_health(self):
        """Update the health dashboard section"""
        if not self.health_monitor:
            self.layout["health"].update(
                Panel("Health Monitor Not Available", border_style="yellow")
            )
            return
            
        try:
            statuses = self.health_monitor.get_all_service_statuses()
            
            table = Table(title="Service Health", box=box.ROUNDED)
            table.add_column("Service")
            table.add_column("Status")
            table.add_column("Latency")
            
            for service_id, data in statuses.items():
                display_name = data.get("display_name", service_id)
                status = data.get("status", "unknown")
                latency = data.get("latency_ms", "-")
                
                status_color = {
                    "ok": "green",
                    "warning": "yellow",
                    "error": "red",
                    "unknown": "grey"
                }.get(status, "white")
                
                table.add_row(
                    display_name,
                    f"[{status_color}]{status.upper()}[/]",
                    f"{latency} ms" if isinstance(latency, (int, float)) else latency
                )
            
            self.layout["health"].update(table)
        except Exception as e:
            self.layout["health"].update(
                Panel(f"Error updating health: {str(e)}", border_style="red")
            )
    
    def _update_stats(self):
        """Update the statistics section"""
        if not self.analytics:
            self.layout["stats"].update(
                Panel("Analytics Not Available", border_style="yellow")
            )
            return
            
        try:
            report = self.analytics.generate_report()
            
            table = Table(title="Contribution Stats", box=box.ROUNDED)
            table.add_column("Metric")
            table.add_column("Value")
            
            table.add_row("Current Streak", f"{report.get('current_streak', 0)} days")
            table.add_row("Daily Average", f"{report.get('daily_average', 0):.1f}")
            table.add_row("Success Probability", f"{report.get('success_probability', 0)*100:.1f}%")
            
            repo_activity = report.get('repo_activity', {})
            if repo_activity:
                repos = ", ".join(list(repo_activity.keys())[:3])
                if len(repo_activity) > 3:
                    repos += f"... (+{len(repo_activity) - 3} more)"
                table.add_row("Active Repos", repos)
            
            self.layout["stats"].update(table)
        except Exception as e:
            self.layout["stats"].update(
                Panel(f"Error updating stats: {str(e)}", border_style="red")
            )
    
    def _update_content(self):
        """Update the main content section"""
        self.layout["content"].update(
            Panel("Ready for commands", border_style="green")
        )
    
    def display_progress(self, task_name, total_steps):
        """
        Display a progress bar for a task
        
        Args:
            task_name: Name of the task
            total_steps: Total number of steps
        
        Returns:
            Progress context manager
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("• [bold]{task.completed}/{task.total}"),
            expand=True
        )
        
        task_id = progress.add_task(task_name, total=total_steps)
        
        class ProgressManager:
            def __init__(self, progress, task_id):
                self.progress = progress
                self.task_id = task_id
                
            def advance(self, steps=1):
                self.progress.update(self.task_id, advance=steps)
                
            def update(self, **kwargs):
                self.progress.update(self.task_id, **kwargs)
        
        self.layout["content"].update(progress)
        return ProgressManager(progress, task_id)
    
    def prompt_for_input(self, prompt_text, choices=None):
        """
        Prompt the user for input
        
        Args:
            prompt_text: Text to display for the prompt
            choices: List of choices (optional)
            
        Returns:
            User input
        """
        if self.live:
            self.live.stop()
            
        result = Prompt.ask(prompt_text, choices=choices) if choices else Prompt.ask(prompt_text)
        
        if self.running:
            self.live = Live(self.layout, refresh_per_second=4, screen=True)
            self.live.start()
            
        return result
    
    def confirm(self, question):
        """
        Ask for user confirmation
        
        Args:
            question: Question to confirm
            
        Returns:
            Boolean indicating user confirmation
        """
        if self.live:
            self.live.stop()
            
        result = Confirm.ask(question)
        
        if self.running:
            self.live = Live(self.layout, refresh_per_second=4, screen=True)
            self.live.start()
            
        return result
    
    def display_code(self, code, language="python"):
        """
        Display syntax-highlighted code
        
        Args:
            code: Code to display
            language: Programming language for syntax highlighting
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.layout["content"].update(Panel(syntax, title=f"{language} Code", border_style="green"))

def main():
    """Main function for testing the CLI interface"""
    cli = InteractiveCLI()
    cli.start()

if __name__ == "__main__":
    main() 