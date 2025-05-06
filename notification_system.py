"""
Notification System for GitHub Contribution Hack

Provides notification capabilities through multiple channels
(email, desktop, webhooks).
"""
import os
import json
import logging
import smtplib
import requests
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime, timedelta

from config_loader import ConfigManager

# Configure logger
logger = logging.getLogger(__name__)

class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        
    def send(self, title: str, message: str, level: str = "info", **kwargs) -> bool:
        """
        Send a notification
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error)
            **kwargs: Additional arguments specific to the channel
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            return self._send_impl(title, message, level, **kwargs)
        except Exception as e:
            logger.error(f"Failed to send notification via {self.name}: {str(e)}")
            return False
            
    def _send_impl(self, title: str, message: str, level: str, **kwargs) -> bool:
        """Implementation of sending a notification"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def enable(self):
        """Enable the notification channel"""
        self.enabled = True
        
    def disable(self):
        """Disable the notification channel"""
        self.enabled = False


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, 
                 sender: str, recipients: List[str]):
        """
        Initialize email notification channel
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            sender: Sender email address
            recipients: List of recipient email addresses
        """
        super().__init__("email")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender
        self.recipients = recipients
        
    def _send_impl(self, title: str, message: str, level: str, **kwargs) -> bool:
        """Send email notification"""
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)
        msg['Subject'] = f"[GitHub Contribution] {title}"
        
        # Format email body
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ color: #0366d6; font-size: 20px; font-weight: bold; }}
                .message {{ margin-top: 10px; margin-bottom: 10px; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
                .{level} {{ padding: 10px; border-radius: 5px; }}
                .info {{ background-color: #f1f8ff; border-left: 4px solid #0366d6; }}
                .warning {{ background-color: #fffbdd; border-left: 4px solid #b08800; }}
                .error {{ background-color: #ffdce0; border-left: 4px solid #d73a49; }}
                .timestamp {{ color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">{title}</div>
            <div class="timestamp">Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="message {level}">{message}</div>
            <div class="footer">
                This is an automated notification from GitHub Contribution Hack.
                <br>
                To configure notification settings, please update your configuration file.
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_message, 'html'))
        
        # Connect to SMTP server and send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    def __init__(self, webhook_url: str, custom_headers: Optional[Dict[str, str]] = None):
        """
        Initialize webhook notification channel
        
        Args:
            webhook_url: Webhook URL
            custom_headers: Custom HTTP headers (optional)
        """
        super().__init__("webhook")
        self.webhook_url = webhook_url
        self.custom_headers = custom_headers or {}
        
    def _send_impl(self, title: str, message: str, level: str, **kwargs) -> bool:
        """Send webhook notification"""
        payload = {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "source": "github-contribution-hack"
        }
        
        # Add any custom fields from kwargs
        payload.update({k: v for k, v in kwargs.items() if k not in payload})
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GitHub-Contribution-Hack/1.0"
        }
        headers.update(self.custom_headers)
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        return response.status_code >= 200 and response.status_code < 300


class DesktopNotificationChannel(NotificationChannel):
    """Desktop notification channel"""
    
    def __init__(self):
        """Initialize desktop notification channel"""
        super().__init__("desktop")
        self._check_availability()
        
    def _check_availability(self):
        """Check if desktop notifications are available"""
        try:
            import notify2
            notify2.init("GitHub Contribution Hack")
            self.notify2 = notify2
            self.available = True
        except ImportError:
            try:
                from plyer import notification
                self.notification = notification
                self.available = True
            except ImportError:
                logger.warning("Desktop notifications not available. Install either 'notify2' or 'plyer'.")
                self.available = False
        
    def _send_impl(self, title: str, message: str, level: str, **kwargs) -> bool:
        """Send desktop notification"""
        if not self.available:
            return False
            
        try:
            if hasattr(self, 'notify2'):
                notification = self.notify2.Notification(title, message)
                notification.show()
                return True
            elif hasattr(self, 'notification'):
                self.notification.notify(
                    title=title,
                    message=message,
                    app_name="GitHub Contribution Hack",
                    timeout=kwargs.get('timeout', 10)
                )
                return True
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {str(e)}")
            return False
        
        return False


class NotificationManager:
    """Manages notification channels and routing"""
    
    def __init__(self, manager_config: Optional[Dict] = None):
        """Initialize notification manager

        Args:
            manager_config: Configuration for the manager itself (e.g. history size, routing)
        """
        self.channels = {}
        self.notification_history = []
        self.notification_count = 0
        self.throttle_rules = {}
        
        # Level-based routing (example: errors to email and webhook, info to desktop)
        self.level_routing = {
            "info": ["desktop"], # Default for info
            "warning": ["desktop", "email"], # Default for warning
            "error": ["email", "webhook"] # Default for error
        }
        self.max_history = 100 # Default max history

        if manager_config:
            self.max_history = manager_config.get('max_history', self.max_history)
            self.level_routing.update(manager_config.get('level_routing', {}))
            # Load throttle rules from config
            for rule_name, rule_config in manager_config.get('throttle_rules', {}).items():
                self.set_throttle_rule(
                    rule_config.get('pattern', f'^{rule_name}$'), # Use rule_name as pattern if not specified
                    rule_config.get('max_count', 5),
                    rule_config.get('time_window_seconds', 3600)
                )
        
    def add_channel(self, channel: NotificationChannel):
        """
        Add a notification channel
        
        Args:
            channel: NotificationChannel instance
        """
        self.channels[channel.name] = channel
        logger.info(f"Added notification channel: {channel.name}")
        
    def remove_channel(self, channel_name: str):
        """
        Remove a notification channel
        
        Args:
            channel_name: Name of the channel to remove
        """
        if channel_name in self.channels:
            del self.channels[channel_name]
            logger.info(f"Removed notification channel: {channel_name}")
        
    def notify(self, title: str, message: str, level: str = "info", 
               channels: Optional[List[str]] = None, **kwargs) -> Dict[str, bool]:
        """
        Send a notification to specified channels
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error)
            channels: List of channel names to use (None for all)
            **kwargs: Additional arguments for channels
            
        Returns:
            Dictionary of channel names and success status
        """
        if not self._check_throttle(title, level):
            logger.info(f"Notification throttled: {title}")
            return {}
            
        target_channel_names = set(channels) if channels is not None else set()
        if not target_channel_names: # If no specific channels requested, use level-based routing
            target_channel_names.update(self.level_routing.get(level, []))
            # Fallback to all channels if level has no specific routing and no channels were given
            if not target_channel_names and channels is None:
                target_channel_names.update(self.channels.keys())

        if not target_channel_names:
            logger.warning(f"No target channels for notification '{title}' (level: {level}). Check routing config.")
            self._record_notification(title, message, level, {}, "No target channels")
            return {}

        results = {}
        
        for channel_name in target_channel_names:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                results[channel_name] = channel.send(title, message, level, **kwargs)
                
        self._record_notification(title, message, level, results)
        return results
        
    def _record_notification(self, title: str, message: str, level: str, 
                            results: Dict[str, bool], status_message: Optional[str] = None):
        """Record notification attempt to history"""
        notification = {
            "id": self.notification_count,
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "level": level,
            "results": results,
            "status_message": status_message
        }
        
        self.notification_history.append(notification)
        self.notification_count += 1
        
        # Trim history if it exceeds max size
        if len(self.notification_history) > self.max_history:
            self.notification_history.pop(0)
            
    def get_notification_history(self, limit: int = None) -> List[Dict]:
        """
        Get notification history
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of notification records
        """
        if limit:
            return self.notification_history[-limit:]
        return self.notification_history
        
    def set_throttle_rule(self, pattern: str, max_count: int, time_window: int):
        """
        Set a notification throttle rule
        
        Args:
            pattern: String pattern to match notification titles
            max_count: Maximum number of notifications in the time window
            time_window: Time window in seconds
        """
        self.throttle_rules[pattern] = {
            "max_count": max_count,
            "time_window": time_window,
            "history": []
        }
        
    def _check_throttle(self, title: str, level: str) -> bool:
        """
        Check if a notification should be throttled
        
        Args:
            title: Notification title
            level: Notification level
            
        Returns:
            True if the notification should be sent, False if it should be throttled
        """
        # Critical level notifications are never throttled
        if level == "error":
            return True
            
        now = datetime.now()
        
        for pattern, rule in self.throttle_rules.items():
            if pattern in title:
                # Clean old entries
                rule["history"] = [
                    ts for ts in rule["history"] 
                    if now - ts < timedelta(seconds=rule["time_window"])
                ]
                
                # Check if limit exceeded
                if len(rule["history"]) >= rule["max_count"]:
                    return False
                    
                # Record this notification
                rule["history"].append(now)
                
        return True

# Example setup for the notification system
def setup_notifications(config_manager: ConfigManager) -> Optional[NotificationManager]:
    """
    Set up notification channels based on configuration
    
    Args:
        config_manager: The ConfigManager instance providing all configurations.
        
    Returns:
        NotificationManager instance or None if notifications are disabled or misconfigured.
    """
    if not config_manager.get('notifications.enabled', False):
        logger.info("Notification system is disabled in the configuration.")
        return None

    # Get the general notification manager settings
    manager_settings = config_manager.get('notifications.manager', {})
    manager = NotificationManager(manager_config=manager_settings)
    
    # Email channel
    email_config = config_manager.get('notifications.email')
    if email_config and email_config.get('enabled', False):
        try:
            email_channel = EmailNotificationChannel(
                smtp_server=email_config['smtp_server'],
                smtp_port=int(email_config.get('smtp_port', 587)), # Ensure int, provide default
                username=email_config['username'],
                password=email_config['password'],
                sender=email_config['sender'],
                recipients=email_config['recipients']
            )
            manager.add_channel(email_channel)
            logger.info("Email notification channel configured.")
        except KeyError as e:
            logger.error(f"Missing key in email configuration: {e}. Email channel disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize EmailNotificationChannel: {str(e)}. Email channel disabled.")

    # Webhook channel
    webhook_config = config_manager.get('notifications.webhook')
    if webhook_config and webhook_config.get('enabled', False):
        if webhook_config.get('url'):
            try:
                webhook_channel = WebhookNotificationChannel(
                    webhook_url=webhook_config['url'],
                    custom_headers=webhook_config.get('custom_headers')
                )
                manager.add_channel(webhook_channel)
                logger.info("Webhook notification channel configured.")
            except Exception as e:
                logger.error(f"Failed to initialize WebhookNotificationChannel: {str(e)}. Webhook channel disabled.")
        else:
            logger.warning("Webhook URL not provided. Webhook channel disabled.")

    # Desktop notification channel
    desktop_config = config_manager.get('notifications.desktop')
    if desktop_config and desktop_config.get('enabled', False):
        try:
            desktop_channel = DesktopNotificationChannel()
            if desktop_channel.available: # Only add if underlying libraries are present
                manager.add_channel(desktop_channel)
                logger.info("Desktop notification channel configured.")
            else:
                logger.warning("Desktop notification channel enabled in config, but dependencies are missing. Channel disabled.")
        except Exception as e:
             logger.error(f"Failed to initialize DesktopNotificationChannel: {str(e)}. Desktop channel disabled.")

    if not manager.channels:
        logger.warning("No notification channels were successfully configured, though notifications are enabled.")
        return None # Or return manager if partial functionality is acceptable
        
    return manager


def main():
    """Example usage of the notification system (for testing)"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a dummy config.yml for testing setup_notifications
    dummy_config_data = {
        'notifications': {
            'enabled': True,
            'manager': {
                'max_history': 50,
                'level_routing': {
                    'info': ['desktop'],
                    'error': ['email', 'webhook']
                },
                'throttle_rules': {
                    'frequent_error': {
                        'pattern': '.*ErrorOccurred.*', # Regex pattern for title
                        'max_count': 3,
                        'time_window_seconds': 60 
                    }
                }
            },
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.example.com', # Replace with your SMTP server
                'smtp_port': 587,
                'username': 'user@example.com',    # Replace with your username
                'password': 'your_password',       # Replace with your password
                'sender': 'notifications@example.com',
                'recipients': ['recipient1@example.com', 'recipient2@example.com']
            },
            'webhook': {
                'enabled': True,
                'url': 'https://webhook.site/your-unique-url', # Replace with a test webhook URL
                'custom_headers': {'X-API-Key': 'secret-key'}
            },
            'desktop': {
                'enabled': True
            }
        }
    }
    # Create a ConfigManager instance with this dummy data
    # For a real scenario, ConfigManager would load from 'config.yml'
    class MockConfigManager:
        def __init__(self, data):
            self.data = data
        def get(self, key, default=None):
            keys = key.split('.')
            val = self.data
            try:
                for k in keys:
                    val = val[k]
                return val
            except KeyError:
                return default

    test_config_manager = MockConfigManager(dummy_config_data)

    notification_mgr = setup_notifications(test_config_manager)
    
    if notification_mgr:
        logger.info("NotificationManager initialized.")
        
        # Test sending notifications
        results_info = notification_mgr.notify(
            "Test Info Notification", 
            "This is an informational message.", 
            level="info"
        )
        logger.info(f"Info notification results: {results_info}")
        
        time.sleep(1) # ensure different timestamp
        results_warning = notification_mgr.notify(
            "Test Warning Notification", 
            "This is a warning message.", 
            level="warning", 
            channels=['email'] # Override routing, send only to email
        )
        logger.info(f"Warning notification results: {results_warning}")

        time.sleep(1)
        results_error = notification_mgr.notify(
            "Test Error Notification: ErrorOccurredEvent", 
            "This is a critical error message.", 
            level="error",
            details={"code": 500, "component": "API"}
        )
        logger.info(f"Error notification results: {results_error}")

        # Test throttling
        for i in range(5):
            time.sleep(0.2)
            throttled_results = notification_mgr.notify(
                f"Frequent ErrorOccurredEvent #{i+1}", 
                "Testing throttle rule.", 
                level="error"
            )
            logger.info(f"Throttled Error notification {i+1} results: {throttled_results}")

        # Test history
        history = notification_mgr.get_notification_history(limit=5)
        logger.info("Recent notification history (last 5):")
        for item in history:
            logger.info(f"  - {item['timestamp']} [{item['level'].upper()}] {item['title']}: Sent to {item['sent_to']}")
    else:
        logger.warning("NotificationManager failed to initialize.")

if __name__ == "__main__":
    main() 