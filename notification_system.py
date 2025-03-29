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
    
    def __init__(self):
        """Initialize notification manager"""
        self.channels = {}
        self.notification_history = []
        self.max_history = 100
        self.notification_count = 0
        self.throttle_rules = {}
        
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
            
        target_channels = channels or list(self.channels.keys())
        results = {}
        
        for channel_name in target_channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                results[channel_name] = channel.send(title, message, level, **kwargs)
                
        # Record notification
        self._record_notification(title, message, level, results)
                
        return results
        
    def _record_notification(self, title: str, message: str, level: str, 
                            results: Dict[str, bool]):
        """Record a notification in history"""
        notification = {
            "id": self.notification_count,
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "level": level,
            "results": results
        }
        
        self.notification_history.append(notification)
        self.notification_count += 1
        
        # Trim history if needed
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
            
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
def setup_notifications(config: Dict) -> NotificationManager:
    """
    Set up notification manager based on configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured NotificationManager instance
    """
    manager = NotificationManager()
    
    # Set up channels based on configuration
    notification_config = config.get('notifications', {})
    
    # Email notifications
    if notification_config.get('email', {}).get('enabled', False):
        email_config = notification_config['email']
        manager.add_channel(EmailNotificationChannel(
            smtp_server=email_config.get('smtp_server', ''),
            smtp_port=email_config.get('smtp_port', 587),
            username=email_config.get('username', ''),
            password=email_config.get('password', ''),
            sender=email_config.get('sender', ''),
            recipients=email_config.get('recipients', [])
        ))
    
    # Webhook notifications
    if notification_config.get('webhook', {}).get('enabled', False):
        webhook_config = notification_config['webhook']
        manager.add_channel(WebhookNotificationChannel(
            webhook_url=webhook_config.get('url', ''),
            custom_headers=webhook_config.get('headers', {})
        ))
    
    # Desktop notifications
    if notification_config.get('desktop', {}).get('enabled', False):
        manager.add_channel(DesktopNotificationChannel())
    
    # Set up throttling rules
    throttle_rules = notification_config.get('throttle_rules', [])
    for rule in throttle_rules:
        manager.set_throttle_rule(
            pattern=rule.get('pattern', ''),
            max_count=rule.get('max_count', 5),
            time_window=rule.get('time_window', 3600)
        )
    
    return manager


def main():
    """Test notification system"""
    manager = NotificationManager()
    
    # Add a desktop notification channel
    manager.add_channel(DesktopNotificationChannel())
    
    # Send a test notification
    results = manager.notify(
        "Test Notification",
        "This is a test notification from the GitHub Contribution Hack.",
        "info"
    )
    
    print(f"Notification results: {results}")
    print(f"Notification history: {manager.get_notification_history()}")

if __name__ == "__main__":
    main() 