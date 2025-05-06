import unittest
import os
import yaml
import tempfile
import logging
from unittest.mock import patch, MagicMock

from config_loader import ConfigManager

# Suppress logging during tests unless specifically testing logging
logging.disable(logging.CRITICAL)

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        # Create a temporary config file for each test
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml')
        self.test_config_path = self.temp_config_file.name
        self.initial_data = {
            'general': {
                'app_name': 'TestApp',
                'version': '1.0'
            },
            'database': {
                'host': 'localhost',
                'port': 5432
            },
            'features': {
                'feature_a': True,
                'feature_b_threshold': 100
            },
            'simple_key': 'simple_value',
            'list_key': ['item1', 'item2']
        }
        yaml.dump(self.initial_data, self.temp_config_file)
        self.temp_config_file.close() # Close it so ConfigManager can open it

    def tearDown(self):
        if os.path.exists(self.test_config_path):
            os.unlink(self.test_config_path)
        logging.disable(logging.NOTSET) # Re-enable logging

    def test_load_config_success(self):
        """Test successful loading of an existing config file."""
        cm = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(cm.config, self.initial_data)
        self.assertEqual(cm.get('general.app_name'), 'TestApp')

    def test_load_config_file_not_found(self):
        """Test loading when config file does not exist."""
        non_existent_path = "/tmp/non_existent_config.yml"
        if os.path.exists(non_existent_path):
            os.unlink(non_existent_path) # Ensure it doesn't exist
        
        with patch.object(logging.getLoggerClass(), 'warning') as mock_log_warning:
            cm = ConfigManager(config_path=non_existent_path)
            self.assertEqual(cm.config, {}) # Should initialize to empty dict
            mock_log_warning.assert_called_once_with(
                f"Configuration file {non_existent_path} not found. Initializing with empty config."
            )

    def test_load_config_empty_yaml_file(self):
        """Test loading an empty YAML file."""
        empty_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml')
        empty_file.close()
        cm = ConfigManager(config_path=empty_file.name)
        self.assertEqual(cm.config, {}) # Should be an empty dict if YAML is None
        os.unlink(empty_file.name)

    def test_load_config_invalid_yaml_file(self):
        """Test loading a file with invalid YAML content."""
        invalid_yaml_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml')
        invalid_yaml_file.write("general: { app_name: TestApp, version: 1.0") # Missing closing brace
        invalid_yaml_file.close()
        
        with patch.object(logging.getLoggerClass(), 'error') as mock_log_error:
            cm = ConfigManager(config_path=invalid_yaml_file.name)
            self.assertEqual(cm.config, {}) # Fallback to empty dict
            self.assertTrue("Error parsing YAML" in mock_log_error.call_args[0][0])
        os.unlink(invalid_yaml_file.name)

    def test_get_existing_top_level_key(self):
        cm = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(cm.get('simple_key'), 'simple_value')

    def test_get_existing_nested_key(self):
        cm = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(cm.get('general.app_name'), 'TestApp')
        self.assertEqual(cm.get('database.port'), 5432)

    def test_get_non_existent_key_with_default(self):
        cm = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(cm.get('non.existent.key', 'default_val'), 'default_val')

    def test_get_non_existent_key_without_default(self):
        cm = ConfigManager(config_path=self.test_config_path)
        self.assertIsNone(cm.get('non.existent.key'))

    def test_get_list_key(self):
        cm = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(cm.get('list_key'), ['item1', 'item2'])

    def test_set_new_top_level_key(self):
        cm = ConfigManager(config_path=self.test_config_path)
        cm.set('new_top_key', 'new_top_value')
        self.assertEqual(cm.get('new_top_key'), 'new_top_value')
        self.assertEqual(cm.config['new_top_key'], 'new_top_value')

    def test_set_new_nested_key(self):
        cm = ConfigManager(config_path=self.test_config_path)
        cm.set('new_parent.new_child', 'nested_value')
        self.assertEqual(cm.get('new_parent.new_child'), 'nested_value')
        self.assertEqual(cm.config['new_parent']['new_child'], 'nested_value')

    def test_set_overwrite_existing_key(self):
        cm = ConfigManager(config_path=self.test_config_path)
        cm.set('simple_key', 'overwritten_value')
        self.assertEqual(cm.get('simple_key'), 'overwritten_value')
        cm.set('database.host', 'newdb.example.com')
        self.assertEqual(cm.get('database.host'), 'newdb.example.com')

    def test_save_config_and_reload(self):
        cm1 = ConfigManager(config_path=self.test_config_path)
        cm1.set('general.version', '2.0')
        cm1.set('new_feature.enabled', True)
        save_result = cm1.save_config()
        self.assertTrue(save_result)

        # Create a new ConfigManager instance to reload the saved config
        cm2 = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(cm2.get('general.version'), '2.0')
        self.assertEqual(cm2.get('new_feature.enabled'), True)
        self.assertEqual(cm2.get('general.app_name'), 'TestApp') # Ensure old data still there

    def test_get_all_config_returns_copy(self):
        cm = ConfigManager(config_path=self.test_config_path)
        all_conf = cm.get_all_config()
        self.assertEqual(all_conf, self.initial_data)
        # Modify the returned dict and check if original is unchanged
        all_conf['simple_key'] = 'modified_in_copy'
        self.assertEqual(cm.get('simple_key'), 'simple_value')

    def test_update_config_simple_merge(self):
        cm = ConfigManager(config_path=self.test_config_path)
        update_data = {
            'simple_key': 'updated_simple',
            'general': {'version': '1.1'}, # Overwrites version, keeps app_name
            'new_top_level': {'sub_key': 'sub_value'}
        }
        cm.update_config(update_data)

        self.assertEqual(cm.get('simple_key'), 'updated_simple')
        self.assertEqual(cm.get('general.version'), '1.1')
        self.assertEqual(cm.get('general.app_name'), 'TestApp') # Should persist
        self.assertEqual(cm.get('new_top_level.sub_key'), 'sub_value')

    def test_update_config_deep_merge_new_dicts(self):
        cm = ConfigManager(config_path=self.test_config_path)
        update_data = {
            'database': {'user': 'admin', 'timeout': 30}, # Adds user, timeout to existing db dict
            'features': {'feature_c': {'enabled': False, 'level': 5}} # Adds new feature_c dict
        }
        cm.update_config(update_data)

        self.assertEqual(cm.get('database.host'), 'localhost') # Original persisted
        self.assertEqual(cm.get('database.port'), 5432)       # Original persisted
        self.assertEqual(cm.get('database.user'), 'admin')
        self.assertEqual(cm.get('database.timeout'), 30)

        self.assertTrue(cm.get('features.feature_a')) # Original persisted
        self.assertEqual(cm.get('features.feature_c.enabled'), False)
        self.assertEqual(cm.get('features.feature_c.level'), 5)

    def test_update_config_overwrites_non_dict_with_dict(self):
        cm = ConfigManager(config_path=self.test_config_path)
        # 'simple_key' is currently a string 'simple_value'
        update_data = {
            'simple_key': {'new_sub_key': 'new_sub_value'}
        }
        cm.update_config(update_data)
        self.assertEqual(cm.get('simple_key.new_sub_key'), 'new_sub_value')
        self.assertIsInstance(cm.get('simple_key'), dict)

    def test_update_config_overwrites_dict_with_non_dict(self):
        cm = ConfigManager(config_path=self.test_config_path)
        # 'general' is currently a dict
        update_data = {
            'general': 'now_a_string'
        }
        cm.update_config(update_data)
        self.assertEqual(cm.get('general'), 'now_a_string')
        self.assertIsInstance(cm.get('general'), str)

    def test_thread_safety_basic(self):
        """A basic check for thread safety (actual concurrency testing is complex)."""
        # This test mainly ensures the RLock is used and doesn't deadlock on simple ops.
        # True concurrency testing requires more specialized tools/frameworks.
        cm = ConfigManager(config_path=self.test_config_path)
        
        # Simulate multiple threads reading and writing by calling methods rapidly.
        # This is not a guarantee of thread safety under heavy load but a sanity check.
        for i in range(100):
            cm.set(f'threaded_key_{i}', i)
            val = cm.get(f'threaded_key_{i % 10}', 0)
            cm.update_config({'counter': i})
        cm.save_config()

        # Verify some final state
        self.assertEqual(cm.get('threaded_key_99'), 99)
        self.assertEqual(cm.get('counter'), 99)
        
        # Load fresh and check saved state
        cm_reloaded = ConfigManager(config_path=self.test_config_path)
        self.assertEqual(cm_reloaded.get('threaded_key_99'), 99)
        self.assertEqual(cm_reloaded.get('counter'), 99)

if __name__ == '__main__':
    unittest.main() 