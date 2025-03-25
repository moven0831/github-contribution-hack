"""
Health monitoring module for GitHub Contribution Hack

Monitors health and availability of dependencies like MCP API
and GitHub API. Provides alerting and status reporting.
"""
import os
import time
import json
import logging
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable
import queue
import heapq
from concurrent.futures import ThreadPoolExecutor
import functools

# Configure logger
logger = logging.getLogger(__name__)

class HealthStatus:
    """Status constants for health checks"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

class ServiceMonitor:
    """Monitor for service health and availability"""
    
    def __init__(self, 
                 check_interval: int = 300,  # 5 minutes
                 history_size: int = 100,    # Keep last 100 checks
                 alert_threshold: int = 3,   # Alert after 3 consecutive failures
                 max_workers: int = 5):      # Maximum number of worker threads
        """
        Initialize health monitor
        
        Args:
            check_interval: Interval between checks in seconds
            history_size: Number of check results to keep in history
            alert_threshold: Number of consecutive failures before alerting
            max_workers: Maximum number of workers for parallel health checks
        """
        self.check_interval = check_interval
        self.history_size = history_size
        self.alert_threshold = alert_threshold
        self.max_workers = max_workers
        
        # Service status history with fixed size (using deque is more efficient)
        from collections import deque
        self.service_history = {}
        
        # Registered health check functions
        self.health_checks = {}
        
        # Alerting functions
        self.alert_handlers = []
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Monitor thread
        self.monitor_thread = None
        self.should_stop = threading.Event()
        
        # Task queue for scheduled checks
        self.task_queue = queue.PriorityQueue()
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Cache for health check results
        self.result_cache = {}
        self.cache_ttl = 60  # Cache results for 60 seconds
        
        # Register default health checks
        self._register_default_checks()
        
        logger.info("Health monitor initialized")
    
    def _register_default_checks(self):
        """Register default health check functions"""
        # MCP API health check
        if os.environ.get("MCP_API_KEY") and os.environ.get("MCP_API_ENDPOINT"):
            self.register_health_check(
                "mcp-api", 
                self._check_mcp_api_health,
                "MCP API Service"
            )
        
        # GitHub API health check
        if os.environ.get("GITHUB_TOKEN"):
            self.register_health_check(
                "github-api",
                self._check_github_api_health,
                "GitHub API Service"
            )
    
    def register_health_check(self, 
                             service_id: str, 
                             check_func: Callable[[], Dict], 
                             display_name: str,
                             service_url: Optional[str] = None):
        """
        Register a health check function
        
        Args:
            service_id: Unique identifier for the service
            check_func: Function that performs the health check
            display_name: Human-readable service name
            service_url: URL of the service (optional)
        """
        with self.lock:
            self.health_checks[service_id] = {
                "func": check_func,
                "display_name": display_name,
                "service_url": service_url
            }
            self.service_history[service_id] = []
            logger.info(f"Registered health check for {display_name}")
    
    def register_alert_handler(self, handler: Callable[[str, Dict], None]):
        """
        Register an alert handler function
        
        Args:
            handler: Function that handles alerts
        """
        with self.lock:
            self.alert_handlers.append(handler)
            logger.info(f"Added alert handler: {handler.__name__}")
    
    def _check_mcp_api_health(self) -> Dict:
        """
        Check MCP API health
        
        Returns:
            Health check result
        """
        api_key = os.environ.get("MCP_API_KEY")
        api_endpoint = os.environ.get("MCP_API_ENDPOINT", "https://api.mcp.dev/v1")
        
        if not api_key:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": "MCP API key not configured",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Use health/ping endpoint if available
            health_url = f"{api_endpoint}/health/ping"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            response = requests.get(health_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                return {
                    "status": HealthStatus.OK,
                    "message": "MCP API is healthy",
                    "latency_ms": int(response.elapsed.total_seconds() * 1000),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": HealthStatus.ERROR,
                    "message": f"MCP API returned status {response.status_code}",
                    "latency_ms": int(response.elapsed.total_seconds() * 1000),
                    "timestamp": datetime.now().isoformat()
                }
        except requests.exceptions.Timeout:
            return {
                "status": HealthStatus.WARNING,
                "message": "MCP API timeout",
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": HealthStatus.ERROR,
                "message": "MCP API connection error",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.ERROR,
                "message": f"MCP API check error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_github_api_health(self) -> Dict:
        """
        Check GitHub API health
        
        Returns:
            Health check result
        """
        github_token = os.environ.get("GITHUB_TOKEN")
        
        if not github_token:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": "GitHub token not configured",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Check rate limit as a simple health check
            rate_limit_url = "https://api.github.com/rate_limit"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(rate_limit_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                remaining = data["rate"]["remaining"]
                
                # Warning if low on rate limit
                if remaining < 100:
                    status = HealthStatus.WARNING
                    message = f"GitHub API rate limit low: {remaining} remaining"
                else:
                    status = HealthStatus.OK
                    message = f"GitHub API healthy: {remaining} requests remaining"
                
                return {
                    "status": status,
                    "message": message,
                    "rate_limit": data["rate"],
                    "latency_ms": int(response.elapsed.total_seconds() * 1000),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": HealthStatus.ERROR,
                    "message": f"GitHub API returned status {response.status_code}",
                    "latency_ms": int(response.elapsed.total_seconds() * 1000),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": HealthStatus.ERROR,
                "message": f"GitHub API check error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def run_health_checks(self) -> Dict[str, Dict]:
        """
        Run all registered health checks in parallel
        
        Returns:
            Dictionary of health check results by service ID
        """
        results = {}
        futures = {}
        
        # Submit all health checks to the thread pool
        with self.lock:
            for service_id, check_info in self.health_checks.items():
                # Check if we have a valid cached result
                current_time = time.time()
                if service_id in self.result_cache:
                    cached_time, cached_result = self.result_cache[service_id]
                    if current_time - cached_time < self.cache_ttl:
                        results[service_id] = cached_result
                        continue
                
                # Submit the check to the executor
                future = self.executor.submit(check_info["func"])
                futures[future] = service_id
        
        # Process the results as they complete
        for future in futures:
            service_id = futures[future]
            try:
                result = future.result(timeout=10)  # 10 seconds timeout
                
                # Update the history
                with self.lock:
                    if service_id not in self.service_history:
                        from collections import deque
                        self.service_history[service_id] = deque(maxlen=self.history_size)
                    self.service_history[service_id].append(result)
                    
                    # Cache the result
                    self.result_cache[service_id] = (time.time(), result)
                
                results[service_id] = result
                
                # Check for alert conditions
                display_name = self.health_checks[service_id]["display_name"]
                self._check_alert_condition(service_id, display_name, result)
                
            except Exception as e:
                logger.error(f"Error running health check for {service_id}: {str(e)}")
                error_result = {
                    "status": HealthStatus.ERROR,
                    "message": f"Health check error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                results[service_id] = error_result
                
                with self.lock:
                    if service_id not in self.service_history:
                        from collections import deque
                        self.service_history[service_id] = deque(maxlen=self.history_size)
                    self.service_history[service_id].append(error_result)
        
        return results
    
    def _check_alert_condition(self, service_id: str, display_name: str, result: Dict):
        """
        Check if alert should be triggered based on result
        
        Args:
            service_id: Service identifier
            display_name: Human-readable service name
            result: Health check result
        """
        if result["status"] in (HealthStatus.ERROR, HealthStatus.WARNING):
            # Check for consecutive failures
            history = self.service_history[service_id]
            
            # Count consecutive failures
            failure_count = 0
            for check in reversed(history):
                if check["status"] in (HealthStatus.ERROR, HealthStatus.WARNING):
                    failure_count += 1
                else:
                    break
            
            if failure_count >= self.alert_threshold:
                # Trigger alert
                alert_data = {
                    "service_id": service_id,
                    "display_name": display_name,
                    "status": result["status"],
                    "message": result["message"],
                    "failure_count": failure_count,
                    "last_check": result
                }
                
                self._trigger_alert(service_id, alert_data)
    
    def _trigger_alert(self, service_id: str, alert_data: Dict):
        """
        Trigger alerts on all registered handlers
        
        Args:
            service_id: Service identifier
            alert_data: Alert data
        """
        logger.warning(f"Service health alert: {service_id} - {alert_data['message']}")
        
        for handler in self.alert_handlers:
            try:
                handler(service_id, alert_data)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
    
    def start_monitoring(self):
        """Start the health monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("Monitoring thread is already running")
            return
        
        self.should_stop.clear()
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop the health monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.info("Stopping health monitoring")
            self.should_stop.set()
            self.monitor_thread.join(timeout=5)
            if self.monitor_thread.is_alive():
                logger.warning("Monitoring thread did not stop cleanly")
            self.monitor_thread = None
            
        # Shutdown the executor
        self.executor.shutdown(wait=False)
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        logger.info("Monitoring loop started")
        
        # Run initial health checks immediately
        self.run_health_checks()
        
        next_run = time.time() + self.check_interval
        
        while not self.should_stop.is_set():
            # Sleep until next check time or stop signal
            current_time = time.time()
            if current_time < next_run:
                # Use Event.wait with timeout instead of time.sleep for more responsive shutdown
                if self.should_stop.wait(min(1.0, next_run - current_time)):
                    break
                continue
                
            # Run health checks
            try:
                self.run_health_checks()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            # Schedule next run
            next_run = time.time() + self.check_interval
    
    def get_service_status(self, service_id: str) -> Dict:
        """
        Get current status of a service
        
        Args:
            service_id: Service identifier
            
        Returns:
            Service status information
        """
        with self.lock:
            if service_id not in self.service_history:
                return {
                    "status": HealthStatus.UNKNOWN,
                    "message": f"Unknown service: {service_id}",
                    "timestamp": datetime.now().isoformat()
                }
            
            history = self.service_history[service_id]
            if not history:
                return {
                    "status": HealthStatus.UNKNOWN,
                    "message": f"No health data for service: {service_id}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get most recent check
            latest = history[-1]
            
            # Add history summary
            status_counts = {
                HealthStatus.OK: 0,
                HealthStatus.WARNING: 0,
                HealthStatus.ERROR: 0,
                HealthStatus.UNKNOWN: 0
            }
            
            for check in history:
                status = check.get("status", HealthStatus.UNKNOWN)
                status_counts[status] += 1
            
            return {
                **latest,
                "service_id": service_id,
                "display_name": self.health_checks[service_id]["display_name"],
                "history_summary": status_counts,
                "history_size": len(history)
            }
    
    def get_all_service_statuses(self) -> Dict[str, Dict]:
        """
        Get current status of all services
        
        Returns:
            Dictionary of service statuses
        """
        result = {}
        with self.lock:
            for service_id in self.health_checks:
                result[service_id] = self.get_service_status(service_id)
        return result
    
    def get_overall_system_status(self) -> Dict:
        """
        Get overall system health status
        
        Returns:
            System health status
        """
        statuses = self.get_all_service_statuses()
        
        # Determine worst status across all services
        if not statuses:
            overall_status = HealthStatus.UNKNOWN
        else:
            status_values = [s["status"] for s in statuses.values()]
            
            if HealthStatus.ERROR in status_values:
                overall_status = HealthStatus.ERROR
            elif HealthStatus.WARNING in status_values:
                overall_status = HealthStatus.WARNING
            elif HealthStatus.UNKNOWN in status_values and len(status_values) == status_values.count(HealthStatus.UNKNOWN):
                overall_status = HealthStatus.UNKNOWN
            else:
                overall_status = HealthStatus.OK
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": statuses,
            "service_count": len(statuses)
        }

# Default health monitor instance
monitor = ServiceMonitor()

def log_alert_handler(service_id: str, alert_data: Dict):
    """
    Default alert handler that logs alerts
    
    Args:
        service_id: Service identifier
        alert_data: Alert data
    """
    logger.warning(
        f"HEALTH ALERT: {alert_data['display_name']} ({service_id}) "
        f"is {alert_data['status']} - {alert_data['message']}"
    )

# Register default alert handler
monitor.register_alert_handler(log_alert_handler) 