// Main JavaScript for GitHub Contribution Hack Web Interface

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
});