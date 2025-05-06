import yaml
import logging
import os
from threading import RLock

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_path='config.yml'):
        self.config_path = config_path
        self.config = {}
        self._lock = RLock()  # For thread-safe operations
        self.load_config()

    def load_config(self):
        """Load configuration from the YAML file."""
        try:
            with self._lock:
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r') as f:
                        self.config = yaml.safe_load(f)
                        if self.config is None: # Handle empty or invalid YAML
                            self.config = {}
                        logger.info(f"Configuration loaded from {self.config_path}")
                else:
                    self.config = {} # Initialize with empty config if file doesn't exist
                    logger.warning(f"Configuration file {self.config_path} not found. Initializing with empty config.")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML in {self.config_path}: {e}")
            # Decide on fallback: raise error, use defaults, or use last known good config
            self.config = {} # Fallback to empty config on parse error
        except IOError as e:
            logger.error(f"Error reading configuration file {self.config_path}: {e}")
            self.config = {} # Fallback to empty config on IO error

    def get(self, key, default=None):
        """Get a configuration value."""
        # Use dict.get for nested keys if key is a path like 'notifications.email.enabled'
        keys = key.split('.')
        value = self.config
        with self._lock:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value

    def set(self, key, value):
        """Set a configuration value. This will update the in-memory config.
           Call save_config() to persist changes to the file."""
        with self._lock:
            keys = key.split('.')
            config_ref = self.config
            for k in keys[:-1]: # Navigate to the parent dictionary
                config_ref = config_ref.setdefault(k, {})
            config_ref[keys[-1]] = value
        logger.info(f"Configuration key '{key}' set. Call save_config() to persist.")


    def save_config(self):
        """Save the current configuration to the YAML file."""
        try:
            with self._lock:
                with open(self.config_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                logger.info(f"Configuration saved to {self.config_path}")
                return True
        except IOError as e:
            logger.error(f"Error writing configuration file {self.config_path}: {e}")
            return False
        except yaml.YAMLError as e:
            logger.error(f"Error formatting YAML for {self.config_path}: {e}")
            return False

    def get_all_config(self):
        """Return a copy of the entire configuration dictionary."""
        with self._lock:
            return self.config.copy() # Return a copy to prevent external modification

    def update_config(self, new_config_dict):
        """Update the configuration with a dictionary. Merges with existing config.
           Call save_config() to persist changes to the file."""
        with self._lock:
            self._deep_merge(self.config, new_config_dict)
        logger.info(f"Configuration updated. Call save_config() to persist.")

    def _deep_merge(self, existing_dict, new_dict):
        """Recursively merge new_dict into existing_dict."""
        for key, value in new_dict.items():
            if isinstance(value, dict) and key in existing_dict and isinstance(existing_dict[key], dict):
                self._deep_merge(existing_dict[key], value)
            else:
                existing_dict[key] = value

# Example usage (optional, for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Create a dummy config.yml for testing
    dummy_config = {
        'general': {
            'app_name': 'MyTestApp',
            'version': '1.0'
        },
        'features': {
            'feature_x': True,
            'feature_y_threshold': 42
        },
        'repositories': ['repo1', 'repo2']
    }
    with open('config.yml', 'w') as f:
        yaml.dump(dummy_config, f)

    config_manager = ConfigManager()

    print("Initial config:", config_manager.get_all_config())
    print("App Name:", config_manager.get('general.app_name'))
    print("Feature Y Threshold:", config_manager.get('features.feature_y_threshold'))
    print("Non-existent key:", config_manager.get('non.existent.key', 'default_value'))
    print("Repositories:", config_manager.get('repositories'))

    config_manager.set('features.feature_z', 'new_value')
    config_manager.set('general.version', '1.1')
    print("Config after set:", config_manager.get_all_config())

    config_manager.save_config()

    # Test loading again
    new_config_manager = ConfigManager()
    print("Reloaded config:", new_config_manager.get_all_config())
    print("Version after save and reload:", new_config_manager.get('general.version'))

    # Test update_config
    update_data = {
        'general': {
            'version': '2.0',
            'description': 'An updated app'
        },
        'features': {
            'feature_x': False
        },
        'new_section': {
            'item_a': 123
        }
    }
    config_manager.update_config(update_data)
    print("Config after update_config:", config_manager.get_all_config())
    config_manager.save_config()

    # Clean up dummy file
    # os.remove('config.yml') 