"""
Web Interface for GitHub Contribution Hack

Provides a web dashboard for monitoring and configuring the contribution system.
Uses Flask for the backend and Bootstrap for the frontend.
"""
import os
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for
from waitress import serve

# Import local modules
from visualization import ContributionVisualizer
from notification_system import NotificationManager, setup_notifications
from config_loader import ConfigManager

# Configure logger
logger = logging.getLogger(__name__)

class WebInterface:
    """Web interface for the GitHub Contribution Hack"""
    
    def __init__(self, config_manager: ConfigManager, host='127.0.0.1', port=5000):
        """
        Initialize the web interface
        
        Args:
            config_manager: Instance of ConfigManager
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.config_manager = config_manager
        self.host = host
        self.port = port
        
        # Create Flask app
        self.app = Flask(__name__, 
                          template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                          static_folder=os.path.join(os.path.dirname(__file__), 'static'))
        
        # Initialize visualization
        try:
            self.visualizer = ContributionVisualizer(self.config_manager)
        except Exception as e:
            logger.error(f"Failed to initialize visualizer: {str(e)}")
            self.visualizer = None
        
        # Initialize notification system
        try:
            self.notification_manager = setup_notifications(self.config_manager)
        except Exception as e:
            logger.error(f"Failed to initialize notification system: {str(e)}")
            self.notification_manager = None
        
        # Server thread
        self.server_thread = None
        self.running = False
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self):
        """Register Flask routes"""
        # Dashboard
        self.app.route('/')(self.dashboard)
        self.app.route('/dashboard')(self.dashboard)
        
        # API endpoints
        self.app.route('/api/stats', methods=['GET'])(self.get_stats)
        self.app.route('/api/config', methods=['GET', 'POST'])(self.handle_config)
        self.app.route('/api/notifications', methods=['GET'])(self.get_notifications)
        self.app.route('/api/vizualization/<viz_type>', methods=['GET'])(self.get_visualization)
        
        # Configuration pages
        self.app.route('/config')(self.config_page)
        self.app.route('/config/repositories', methods=['GET', 'POST'])(self.repositories_config)
        self.app.route('/config/notifications', methods=['GET', 'POST'])(self.notifications_config)
        
        # Actions
        self.app.route('/actions/test-notification', methods=['POST'])(self.test_notification)
        
    def dashboard(self):
        """Render the dashboard page"""
        return render_template('dashboard.html')
    
    def config_page(self):
        """Render the configuration page"""
        return render_template('config.html', config=self.config_manager.get_all_config())
    
    def repositories_config(self):
        """Handle repository configuration"""
        if request.method == 'POST':
            # Update repositories in config
            repositories = request.form.getlist('repositories')
            self.config_manager.set('repositories', repositories)
            self.config_manager.save_config()
            return redirect(url_for('config_page'))
        
        return render_template('repositories_config.html', 
                               repositories=self.config_manager.get('repositories', []))
    
    def notifications_config(self):
        """Handle notification configuration"""
        if request.method == 'POST':
            # Update notification config
            notification_config = {}
            
            # Email settings
            notification_config['email'] = {
                'enabled': 'email_enabled' in request.form,
                'smtp_server': request.form.get('smtp_server', ''),
                'smtp_port': int(request.form.get('smtp_port', 587) or 587),
                'username': request.form.get('smtp_username', ''),
                'password': request.form.get('smtp_password', ''),
                'sender': request.form.get('email_sender', ''),
                'recipients': [r.strip() for r in request.form.get('email_recipients', '').split(',') if r.strip()]
            }
            
            # Webhook settings
            notification_config['webhook'] = {
                'enabled': 'webhook_enabled' in request.form,
                'url': request.form.get('webhook_url', '')
            }
            
            # Desktop notification settings
            notification_config['desktop'] = {
                'enabled': 'desktop_enabled' in request.form
            }
            
            # Update config using ConfigManager
            self.config_manager.set('notifications', notification_config)
            self.config_manager.save_config()
            
            # Reinitialize notification manager
            self.notification_manager = setup_notifications(self.config_manager)
            
            return redirect(url_for('config_page'))
        
        return render_template('notifications_config.html', 
                               notif_config=self.config_manager.get('notifications', {}))
    
    def get_stats(self):
        """API endpoint to get contribution statistics"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'uptime': '12 hours',  # TODO: Calculate actual uptime
            'status': 'running',
        }
        
        # Add database stats if available
        try:
            import sqlite3
            conn = sqlite3.connect('contributions.db')
            cursor = conn.cursor()
            
            # Get total contributions
            cursor.execute('SELECT COUNT(*) FROM contributions')
            stats['total_contributions'] = cursor.fetchone()[0]
            
            # Get counts by repository
            cursor.execute('SELECT repo, COUNT(*) FROM contributions GROUP BY repo')
            stats['repo_counts'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get recent contributions
            cursor.execute('SELECT timestamp, repo FROM contributions ORDER BY timestamp DESC LIMIT 5')
            stats['recent'] = [{'timestamp': row[0], 'repo': row[1]} for row in cursor.fetchall()]
            
            conn.close()
        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            stats['db_error'] = str(e)
        
        return jsonify(stats)
    
    def handle_config(self):
        """API endpoint to get or update configuration"""
        if request.method == 'POST':
            # Update config with JSON data
            updated_config_data = request.json
            if updated_config_data:
                # Merge with existing config using ConfigManager
                self.config_manager.update_config(updated_config_data)
                
                # Save to file
                if self.config_manager.save_config():
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'status': 'error', 'message': 'Failed to save configuration'})
            else:
                return jsonify({'status': 'error', 'message': 'Invalid configuration data'})
        else:
            # Return current config as JSON using ConfigManager
            return jsonify(self.config_manager.get_all_config())
    
    def get_notifications(self):
        """API endpoint to get notification history"""
        if not self.notification_manager:
            return jsonify({'status': 'error', 'message': 'Notification system not available'})
            
        history = self.notification_manager.get_notification_history(20)  # Get last 20 notifications
        return jsonify({
            'status': 'success',
            'notifications': history
        })
    
    def get_visualization(self, viz_type):
        """
        API endpoint to get visualization images
        
        Args:
            viz_type: Type of visualization (heatmap, streak, timeline, repo)
        """
        if not self.visualizer:
            return jsonify({'status': 'error', 'message': 'Visualization system not available'})
            
        try:
            image_path = None
            
            if viz_type == 'heatmap':
                image_path = self.visualizer.generate_heatmap()
            elif viz_type == 'streak':
                image_path = self.visualizer.generate_streak_chart()
            elif viz_type == 'timeline':
                image_path = self.visualizer.generate_activity_timeline()
            elif viz_type == 'repo':
                image_path = self.visualizer.generate_repo_distribution()
            else:
                return jsonify({'status': 'error', 'message': f'Invalid visualization type: {viz_type}'})
                
            if not image_path or not os.path.exists(image_path):
                return jsonify({'status': 'error', 'message': 'Failed to generate visualization'})
                
            # Convert image to base64
            image_data = self.visualizer.get_image_base64(image_path)
            if not image_data:
                return jsonify({'status': 'error', 'message': 'Failed to encode image'})
                
            return jsonify({
                'status': 'success',
                'image': image_data,
                'mime_type': 'image/png'
            })
            
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)})
    
    def test_notification(self):
        """API endpoint to test notifications"""
        if not self.notification_manager:
            return jsonify({'status': 'error', 'message': 'Notification system not available'})
            
        channel = request.form.get('channel', '')
        level = request.form.get('level', 'info')
        
        try:
            channels = [channel] if channel else None
            results = self.notification_manager.notify(
                "Test Notification",
                f"This is a test notification from GitHub Contribution Hack sent at {datetime.now()}.",
                level,
                channels=channels
            )
            
            return jsonify({
                'status': 'success',
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Notification test error: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)})
    
    def start(self, debug=False):
        """
        Start the web interface server
        
        Args:
            debug: Whether to run in debug mode
        """
        if self.running:
            logger.warning("Web interface already running")
            return
            
        def run_server():
            """Run the server in a separate thread"""
            if debug:
                self.app.run(host=self.host, port=self.port, debug=True)
            else:
                # Use waitress for production
                serve(self.app, host=self.host, port=self.port)
                
        if debug:
            # Run directly in the current thread for debug mode
            self.running = True
            run_server()
        else:
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.running = True
            
        logger.info(f"Web interface started at http://{self.host}:{self.port}/")
        
    def stop(self):
        """Stop the web interface server"""
        if not self.running:
            logger.warning("Web interface not running")
            return
            
        self.running = False
        logger.info("Web interface stopped")

def setup_web_interface(config_manager: ConfigManager, host='127.0.0.1', port=5000):
    """
    Set up and return the web interface instance.

    Args:
        config_manager: The ConfigManager instance.
        host: The host for the web server.
        port: The port for the web server.

    Returns:
        WebInterface: The initialized web interface instance.
    """
    # Pass the ConfigManager instance to WebInterface
    interface = WebInterface(config_manager=config_manager, host=host, port=port)
    return interface

# Create app directory structure
def setup_web_interface():
    """Set up directory structure for the web interface"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create templates directory
    templates_dir = os.path.join(base_dir, 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create static directory and subdirectories
    static_dir = os.path.join(base_dir, 'static')
    os.makedirs(os.path.join(static_dir, 'css'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'js'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'img'), exist_ok=True)
    
    # Create basic HTML templates
    with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}GitHub Contribution Hack{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">GitHub Contribution Hack</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/config">Configuration</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <footer class="footer mt-5">
        <div class="container text-center py-3">
            <span class="text-muted">GitHub Contribution Hack</span>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>''')
    
    with open(os.path.join(templates_dir, 'dashboard.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard - GitHub Contribution Hack{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1>Dashboard</h1>
        <div class="card mb-4">
            <div class="card-header">
                System Status
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card text-white bg-success mb-3">
                            <div class="card-body">
                                <h5 class="card-title">Status</h5>
                                <p class="card-text" id="system-status">Loading...</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">Uptime</h5>
                                <p class="card-text" id="system-uptime">Loading...</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">Total Contributions</h5>
                                <p class="card-text" id="total-contributions">Loading...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                Contribution Heatmap
            </div>
            <div class="card-body">
                <img id="heatmap-img" src="" alt="Contribution Heatmap" class="img-fluid">
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                Streak Analysis
            </div>
            <div class="card-body">
                <img id="streak-img" src="" alt="Streak Analysis" class="img-fluid">
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                Activity Timeline
            </div>
            <div class="card-body">
                <img id="timeline-img" src="" alt="Activity Timeline" class="img-fluid">
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                Repository Distribution
            </div>
            <div class="card-body">
                <img id="repo-img" src="" alt="Repository Distribution" class="img-fluid">
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-12">
        <div class="card mb-4">
            <div class="card-header">
                Recent Notifications
            </div>
            <div class="card-body">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Title</th>
                            <th>Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="recent-notifications">
                        <tr>
                            <td colspan="4" class="text-center">Loading...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Load system stats
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('system-status').textContent = data.status || 'Unknown';
            document.getElementById('system-uptime').textContent = data.uptime || 'Unknown';
            document.getElementById('total-contributions').textContent = data.total_contributions || '0';
        });
    
    // Load visualizations
    ['heatmap', 'streak', 'timeline', 'repo'].forEach(vizType => {
        fetch(`/api/vizualization/${vizType}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.image) {
                    document.getElementById(`${vizType}-img`).src = `data:${data.mime_type};base64,${data.image}`;
                }
            });
    });
    
    // Load notifications
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('recent-notifications');
            tableBody.innerHTML = '';
            
            if (data.status === 'success' && data.notifications && data.notifications.length > 0) {
                data.notifications.forEach(notification => {
                    const row = document.createElement('tr');
                    
                    // Format timestamp
                    const timestamp = new Date(notification.timestamp);
                    const formattedTime = timestamp.toLocaleString();
                    
                    // Set level class
                    let levelClass = '';
                    if (notification.level === 'error') {
                        levelClass = 'text-danger';
                    } else if (notification.level === 'warning') {
                        levelClass = 'text-warning';
                    } else if (notification.level === 'info') {
                        levelClass = 'text-info';
                    }
                    
                    row.innerHTML = `
                        <td>${formattedTime}</td>
                        <td>${notification.title}</td>
                        <td class="${levelClass}">${notification.level.toUpperCase()}</td>
                        <td>${notification.message}</td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            } else {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No notifications available</td></tr>';
            }
        });
});
</script>
{% endblock %}''')
    
    with open(os.path.join(templates_dir, 'config.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Configuration - GitHub Contribution Hack{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1>Configuration</h1>
        <div class="card mb-4">
            <div class="card-header">
                Configuration Options
            </div>
            <div class="card-body">
                <div class="list-group">
                    <a href="/config/repositories" class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1">Repositories</h5>
                        </div>
                        <p class="mb-1">Configure repositories for contributions</p>
                    </a>
                    <a href="/config/notifications" class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1">Notifications</h5>
                        </div>
                        <p class="mb-1">Configure notification channels and settings</p>
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-12">
        <div class="card mb-4">
            <div class="card-header">
                Test Notifications
            </div>
            <div class="card-body">
                <form id="test-notification-form">
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <label for="notification-channel" class="form-label">Channel</label>
                            <select class="form-select" id="notification-channel" name="channel">
                                <option value="">All Channels</option>
                                <option value="email">Email</option>
                                <option value="webhook">Webhook</option>
                                <option value="desktop">Desktop</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label for="notification-level" class="form-label">Level</label>
                            <select class="form-select" id="notification-level" name="level">
                                <option value="info">Info</option>
                                <option value="warning">Warning</option>
                                <option value="error">Error</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">&nbsp;</label>
                            <button type="submit" class="btn btn-primary d-block">Send Test Notification</button>
                        </div>
                    </div>
                </form>
                <div id="notification-result" class="alert d-none"></div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-12">
        <div class="card mb-4">
            <div class="card-header">
                Current Configuration
            </div>
            <div class="card-body">
                <pre><code id="config-json">{{ config | tojson(indent=2) }}</code></pre>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Test notification
    document.getElementById('test-notification-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const resultDiv = document.getElementById('notification-result');
        
        fetch('/actions/test-notification', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            resultDiv.classList.remove('d-none', 'alert-success', 'alert-danger');
            
            if (data.status === 'success') {
                resultDiv.classList.add('alert-success');
                resultDiv.textContent = 'Notification sent successfully!';
            } else {
                resultDiv.classList.add('alert-danger');
                resultDiv.textContent = `Error: ${data.message}`;
            }
        })
        .catch(error => {
            resultDiv.classList.remove('d-none');
            resultDiv.classList.add('alert-danger');
            resultDiv.textContent = `Error: ${error.message}`;
        });
    });
});
</script>
{% endblock %}''')
    
    # Create CSS file
    with open(os.path.join(static_dir, 'css', 'styles.css'), 'w') as f:
        f.write('''/* Custom styles for GitHub Contribution Hack */
body {
    background-color: #f8f9fa;
}

.navbar-brand {
    font-weight: bold;
}

.card {
    margin-bottom: 1.5rem;
    border-radius: 0.25rem;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.footer {
    background-color: #f8f9fa;
    border-top: 1px solid #dee2e6;
}''')
    
    # Create JS file
    with open(os.path.join(static_dir, 'js', 'main.js'), 'w') as f:
        f.write('''// Main JavaScript for GitHub Contribution Hack Web Interface

// Auto refresh for dashboard elements
function setupAutoRefresh() {
    // Refresh stats every 60 seconds
    setInterval(function() {
        if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('system-status').textContent = data.status || 'Unknown';
                    document.getElementById('system-uptime').textContent = data.uptime || 'Unknown';
                    document.getElementById('total-contributions').textContent = data.total_contributions || '0';
                });
        }
    }, 60000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupAutoRefresh();
});''')
    
    # Return success
    return True

def main():
    """Main function for testing the web interface"""
    # Set up the web interface
    setup_web_interface()
    
    # Start the web interface
    interface = WebInterface()
    interface.start(debug=True)

if __name__ == "__main__":
    main() 