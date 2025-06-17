#!/usr/bin/env python3
"""
Tests for Configuration Centralization Optimization

This test validates that hardcoded values throughout the codebase have been
successfully moved to the centralized configuration system, addressing 
OPTIMIZATIONS.md Section 10 (Magic Numbers).
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    AppConfig, 
    get_config, 
    StringConstants, 
    ScreenshotConfig, 
    ImageTilingConfig, 
    AIConfig, 
    StorageConfig, 
    PerformanceConfig
)


class TestConfigurationStructure(unittest.TestCase):
    """Test the configuration data structures and basic functionality"""
    
    def test_screenshot_config_defaults(self):
        """Test that screenshot configuration has correct default values"""
        config = ScreenshotConfig()
        
        # Test viewport dimensions (previously hardcoded as 1920x1080)
        self.assertEqual(config.default_width, 1920)
        self.assertEqual(config.default_height, 1080)
        
        # Test timeouts (previously hardcoded as 30000ms and 2000ms)
        self.assertEqual(config.page_load_timeout, 30000)
        self.assertEqual(config.dynamic_content_wait, 2000)
        
        # Test file settings
        self.assertEqual(config.default_extension, ".png")
        self.assertTrue(config.full_page)
    
    def test_image_tiling_config_defaults(self):
        """Test that image tiling configuration has correct default values"""
        config = ImageTilingConfig()
        
        # Test size limits (previously hardcoded as 4000 and 4096)
        self.assertEqual(config.max_height_before_tiling, 4000)
        self.assertEqual(config.max_width_before_tiling, 4096)
        
        # Test tiling parameters (previously hardcoded as 3000 and 200)
        self.assertEqual(config.default_tile_height, 3000)
        self.assertEqual(config.default_overlap, 200)
        
        # Test adaptive settings
        self.assertEqual(config.medium_image_threshold, 8000)
        self.assertEqual(config.medium_tile_height, 3500)
        self.assertEqual(config.medium_overlap, 250)
    
    def test_ai_config_defaults(self):
        """Test that AI configuration has correct default values"""
        config = AIConfig()
        
        # Test token limits (previously hardcoded as 4000)
        self.assertEqual(config.max_tokens, 4000)
        
        # Test model parameters (previously hardcoded as 0.1 and 0.9)
        self.assertEqual(config.temperature, 0.1)
        self.assertEqual(config.top_p, 0.9)
        
        # Test default settings (previously hardcoded)
        self.assertEqual(config.default_model_config_file, "models.json")
        self.assertEqual(config.default_aws_region, "us-east-1")
    
    def test_storage_config_defaults(self):
        """Test that storage configuration has correct default values"""
        config = StorageConfig()
        
        # Test default directories (previously hardcoded)
        self.assertEqual(config.default_screenshots_dir, "screenshots")
        self.assertEqual(config.default_logs_dir, "logs")
        self.assertEqual(config.default_performance_results_dir, "performance_results")
        
        # Test filename patterns
        self.assertIn("{name}", config.baseline_filename_pattern)
        self.assertIn("{id}", config.baseline_filename_pattern)
        self.assertIn(".png", config.baseline_filename_pattern)
        
        self.assertIn("{name}", config.current_filename_pattern)
        self.assertIn("{timestamp}", config.current_filename_pattern)
        
        self.assertEqual(config.metadata_filename, "metadata.json")


class TestStringConstants(unittest.TestCase):
    """Test the centralized string constants"""
    
    def test_file_extensions(self):
        """Test that file extension constants are defined"""
        self.assertEqual(StringConstants.PNG_EXTENSION, ".png")
        self.assertEqual(StringConstants.JSON_EXTENSION, ".json")
    
    def test_error_messages_exist(self):
        """Test that error message templates exist"""
        # Test key error messages that were previously hardcoded
        self.assertIn("aws_credentials_not_found", StringConstants.ERROR_MESSAGES)
        self.assertIn("playwright_not_installed", StringConstants.ERROR_MESSAGES)
        self.assertIn("boto3_not_installed", StringConstants.ERROR_MESSAGES)
        self.assertIn("model_config_not_found", StringConstants.ERROR_MESSAGES)
        
        # Verify they contain placeholders where needed
        self.assertIn("{filename}", StringConstants.ERROR_MESSAGES["model_config_not_found"])
        self.assertIn("{error}", StringConstants.ERROR_MESSAGES["invalid_json_config"])
    
    def test_success_messages_exist(self):
        """Test that success message templates exist"""
        self.assertIn("baseline_stored", StringConstants.SUCCESS_MESSAGES)
        self.assertIn("screenshot_saved", StringConstants.SUCCESS_MESSAGES)
        self.assertIn("model_success", StringConstants.SUCCESS_MESSAGES)
        
        # Verify they contain placeholders
        self.assertIn("{path}", StringConstants.SUCCESS_MESSAGES["screenshot_saved"])
        self.assertIn("{name}", StringConstants.SUCCESS_MESSAGES["baseline_stored"])
    
    def test_info_messages_exist(self):
        """Test that info message templates exist"""
        self.assertIn("url_normalized", StringConstants.INFO_MESSAGES)
        self.assertIn("taking_screenshot", StringConstants.INFO_MESSAGES)
        self.assertIn("large_images_detected", StringConstants.INFO_MESSAGES)
        
        # Verify placeholders
        self.assertIn("{url}", StringConstants.INFO_MESSAGES["url_normalized"])
        self.assertIn("{url}", StringConstants.INFO_MESSAGES["taking_screenshot"])
    
    def test_status_indicators(self):
        """Test that status indicators are defined"""
        self.assertIn("yes", StringConstants.STATUS_INDICATORS)
        self.assertIn("no", StringConstants.STATUS_INDICATORS)
        self.assertIn("available", StringConstants.STATUS_INDICATORS)
        self.assertIn("critical", StringConstants.STATUS_INDICATORS)
        
        # Verify they contain emoji/visual indicators
        self.assertIn("🔴", StringConstants.STATUS_INDICATORS["yes"])
        self.assertIn("🟢", StringConstants.STATUS_INDICATORS["no"])


class TestAppConfigIntegration(unittest.TestCase):
    """Test the main AppConfig class functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config_creation(self):
        """Test that default configuration can be created"""
        config = AppConfig()
        
        # Verify all config sections exist
        self.assertIsInstance(config.screenshot, ScreenshotConfig)
        self.assertIsInstance(config.image_tiling, ImageTilingConfig)
        self.assertIsInstance(config.ai, AIConfig)
        self.assertIsInstance(config.storage, StorageConfig)
        self.assertIsInstance(config.performance, PerformanceConfig)
    
    def test_environment_variable_loading(self):
        """Test that environment variables override defaults"""
        with patch.dict(os.environ, {
            'SCREENSHOT_WIDTH': '1280',
            'SCREENSHOT_HEIGHT': '720',
            'PAGE_LOAD_TIMEOUT': '45000',
            'AWS_DEFAULT_REGION': 'us-west-2'
        }):
            config = AppConfig()
            
            self.assertEqual(config.screenshot.default_width, 1280)
            self.assertEqual(config.screenshot.default_height, 720)
            self.assertEqual(config.screenshot.page_load_timeout, 45000)
            self.assertEqual(config.ai.default_aws_region, 'us-west-2')
    
    def test_config_file_loading(self):
        """Test that configuration can be loaded from JSON file"""
        # Create test config file
        test_config = {
            "screenshot": {
                "default_width": 1600,
                "default_height": 900,
                "page_load_timeout": 25000
            },
            "ai": {
                "max_tokens": 3000,
                "temperature": 0.2
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Load config from file
        config = AppConfig(str(self.config_file))
        
        # Verify values were loaded
        self.assertEqual(config.screenshot.default_width, 1600)
        self.assertEqual(config.screenshot.default_height, 900)
        self.assertEqual(config.screenshot.page_load_timeout, 25000)
        self.assertEqual(config.ai.max_tokens, 3000)
        self.assertEqual(config.ai.temperature, 0.2)
        
        # Verify defaults are preserved for unspecified values
        self.assertEqual(config.screenshot.dynamic_content_wait, 2000)  # Should be default
        self.assertEqual(config.ai.top_p, 0.9)  # Should be default
    
    def test_config_file_saving(self):
        """Test that configuration can be saved to JSON file"""
        config = AppConfig()
        config.screenshot.default_width = 1440
        config.ai.max_tokens = 5000
        
        # Save to file
        config.save_to_file(str(self.config_file))
        
        # Verify file was created and contains correct data
        self.assertTrue(self.config_file.exists())
        
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["screenshot"]["default_width"], 1440)
        self.assertEqual(saved_data["ai"]["max_tokens"], 5000)
        self.assertIn("metadata", saved_data)
        self.assertIn("created", saved_data["metadata"])
    
    def test_get_screenshot_defaults(self):
        """Test that screenshot defaults are properly extracted"""
        config = AppConfig()
        defaults = config.get_screenshot_defaults()
        
        self.assertIn("width", defaults)
        self.assertIn("height", defaults)
        self.assertIn("storage_dir", defaults)
        self.assertIn("aws_region", defaults)
        self.assertIn("config", defaults)
        
        self.assertEqual(defaults["width"], config.screenshot.default_width)
        self.assertEqual(defaults["height"], config.screenshot.default_height)
    
    def test_get_tiling_settings(self):
        """Test that tiling settings are calculated correctly"""
        config = AppConfig()
        
        # Test small image (no tiling needed)
        settings = config.get_tiling_settings(1920, 3000)
        self.assertEqual(settings["tile_height"], 3000)
        self.assertEqual(settings["overlap"], 0)
        
        # Test medium image
        settings = config.get_tiling_settings(1920, 6000)
        self.assertEqual(settings["tile_height"], config.image_tiling.medium_tile_height)
        self.assertEqual(settings["overlap"], config.image_tiling.medium_overlap)
        
        # Test large image
        settings = config.get_tiling_settings(1920, 15000)
        self.assertEqual(settings["tile_height"], config.image_tiling.default_tile_height)
        self.assertEqual(settings["overlap"], config.image_tiling.default_overlap)


class TestGlobalConfigManager(unittest.TestCase):
    """Test the global configuration manager"""
    
    def test_global_config_singleton(self):
        """Test that get_config returns same instance"""
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same instance
        self.assertIs(config1, config2)
    
    def test_force_reload(self):
        """Test that force_reload creates new instance"""
        config1 = get_config()
        config2 = get_config(force_reload=True)
        
        # Should be different instances after force reload
        self.assertIsNot(config1, config2)
        
        # But same type and values
        self.assertEqual(config1.screenshot.default_width, config2.screenshot.default_width)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that the configuration changes don't break existing functionality"""
    
    def test_module_imports(self):
        """Test that all modules can import the config system"""
        try:
            # Test importing config in various modules
            from screenshot_utils import get_config as utils_config
            from image_tiling import get_config as tiling_config
            
            # Both should work and return same instance
            self.assertIs(utils_config(), tiling_config())
            
        except ImportError as e:
            self.fail(f"Configuration import failed: {e}")
    
    def test_default_values_unchanged(self):
        """Test that default behavior is preserved"""
        config = get_config()
        
        # Verify that key defaults match what was previously hardcoded
        self.assertEqual(config.screenshot.default_width, 1920)
        self.assertEqual(config.screenshot.default_height, 1080)
        self.assertEqual(config.screenshot.page_load_timeout, 30000)
        self.assertEqual(config.screenshot.dynamic_content_wait, 2000)
        self.assertEqual(config.ai.max_tokens, 4000)
        self.assertEqual(config.image_tiling.max_height_before_tiling, 4000)
        self.assertEqual(config.image_tiling.default_tile_height, 3000)


if __name__ == "__main__":
    unittest.main() 