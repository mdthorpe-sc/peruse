#!/usr/bin/env python3
"""
Centralized Configuration Management for Screenshot Monitoring Tool

This module consolidates all configuration settings, eliminating magic numbers
and string literals scattered throughout the codebase. It provides a single
source of truth for all configurable values.

For development context, see: DEVELOPMENT_CONTEXT.md
For optimization tracking, see: OPTIMIZATIONS.md Section 10
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ScreenshotConfig:
    """Configuration for screenshot capture settings"""
    # Viewport dimensions
    default_width: int = 1920
    default_height: int = 1080
    
    # Timeouts (in milliseconds)
    page_load_timeout: int = 30000
    dynamic_content_wait: int = 2000
    
    # File settings
    default_extension: str = ".png"
    full_page: bool = True


@dataclass
class ImageTilingConfig:
    """Configuration for image tiling operations"""
    # Size limits for tiling decision
    max_height_before_tiling: int = 4000
    max_width_before_tiling: int = 4096
    
    # Tiling parameters
    default_tile_height: int = 3000
    default_overlap: int = 200
    
    # Adaptive tiling thresholds
    medium_image_threshold: int = 8000
    medium_tile_height: int = 3500
    medium_overlap: int = 250


@dataclass
class AIConfig:
    """Configuration for AI/Bedrock API settings"""
    # Token limits
    max_tokens: int = 4000
    
    # Model parameters
    temperature: float = 0.1
    top_p: float = 0.9
    
    # Default settings
    default_model_config_file: str = "models.json"
    default_aws_region: str = "us-east-1"


@dataclass
class StorageConfig:
    """Configuration for file storage and organization"""
    # Default directories
    default_screenshots_dir: str = "screenshots"
    default_logs_dir: str = "logs"
    default_performance_results_dir: str = "performance_results"
    
    # File naming patterns
    baseline_filename_pattern: str = "{name}_baseline_{id}.png"
    current_filename_pattern: str = "{name}_current_{timestamp}.png"
    report_filename_pattern: str = "{name}_report_{timestamp}.json"
    tile_filename_pattern: str = "tile_{id}_{index:03d}_{start}_{end}.png"
    
    # Metadata
    metadata_filename: str = "metadata.json"


@dataclass
class PerformanceConfig:
    """Configuration for performance testing and monitoring"""
    # Benchmark settings
    default_iterations: int = 1000
    warmup_iterations: int = 100
    config_benchmark_iterations: int = 500
    
    # Performance result storage
    results_timestamp_format: str = "%Y%m%d_%H%M%S"
    session_timestamp_format: str = "%Y%m%d_%H%M%S"


class StringConstants:
    """Centralized string literals and message templates"""
    
    # File extensions
    PNG_EXTENSION = ".png"
    JSON_EXTENSION = ".json"
    
    # Error message templates
    ERROR_MESSAGES = {
        "aws_credentials_not_found": "AWS credentials not found.",
        "aws_credentials_help": [
            "Please configure AWS credentials using:",
            "  aws configure",
            "  or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
        ],
        "playwright_not_installed": "Playwright is not installed.",
        "playwright_install_help": [
            "Please run: pip install playwright",
            "Then run: playwright install"
        ],
        "boto3_not_installed": "boto3 is not installed.",
        "boto3_install_help": ["Please run: pip install boto3"],
        "model_config_not_found": "Model configuration file '{filename}' not found.",
        "invalid_json_config": "Invalid JSON in configuration file '{filename}': {error}",
        "config_load_error": "Error loading configuration file '{filename}': {error}",
        "unknown_model": "Unknown model '{model}'. Available models: {available}",
        "baseline_not_found": "No baseline found for '{name}'. Available baselines:",
        "baseline_file_missing": "Baseline file not found: {path}",
        "screenshot_failed": "Failed to take current screenshot",
        "analysis_error": "Analysis Error: {error}",
        "bedrock_access_denied": "Access denied to Bedrock. Check your AWS permissions.",
        "bedrock_access_help": "Tip: Request access to Claude models in Bedrock console: Model access > Request model access",
        "bedrock_validation_error": "Invalid request to Bedrock. Check your image format and size.",
        "bedrock_validation_help": "Tip: Make sure you have access to {model} in your AWS region.",
        "model_not_found": "Model not found. The inference profile may not be available in your region.",
        "model_not_found_help": "Tip: Try a different AWS region or check model availability."
    }
    
    # Success message templates
    SUCCESS_MESSAGES = {
        "baseline_stored": "Baseline stored for '{name}'",
        "screenshot_saved": "Screenshot saved to: {path}",
        "model_success": "Successfully using model: {model_id}",
        "analysis_complete": "Analysis completed",
        "all_tests_passed": "All tests passed!"
    }
    
    # Info message templates
    INFO_MESSAGES = {
        "url_normalized": "Adding https:// to URL: {url}",
        "large_images_detected": "Large images detected:",
        "using_image_tiling": "Using image tiling for analysis...",
        "tiling_created": "Created {baseline_count} baseline tiles and {current_count} current tiles",
        "create_baseline_help": "To create a baseline for this URL, run:",
        "baseline_command": "   python screenshot_monitor.py baseline {url} --name {name}",
        "cancelled": "Cancelled by user.",
        "taking_screenshot": "Taking screenshot of: {url}",
        "networkidle_failed": "Failed to wait for networkidle: {error}"
    }
    
    # Report section titles
    REPORT_SECTIONS = {
        "change_detection": "CHANGE DETECTION REPORT",
        "performance_benchmark": "PERFORMANCE BENCHMARK SUMMARY",
        "stored_baselines": "Stored Baselines",
        "available_models": "Available Claude Models"
    }
    
    # Status indicators
    STATUS_INDICATORS = {
        "yes": "🔴 YES",
        "no": "🟢 NO",
        "available": "🟢",
        "partially_available": "🟡",
        "unavailable": "🔴",
        "error": "🚨",
        "none": "🟢",
        "minor": "🟡",
        "moderate": "🟠",
        "major": "🔴",
        "critical": "🚨",
        "unknown": "❓"
    }


class AppConfig:
    """Main application configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Optional custom configuration file path
        """
        # Load default configurations
        self.screenshot = ScreenshotConfig()
        self.image_tiling = ImageTilingConfig()
        self.ai = AIConfig()
        self.storage = StorageConfig()
        self.performance = PerformanceConfig()
        
        # Load custom configuration if provided
        if config_file:
            self.load_from_file(config_file)
        else:
            # Try to load from default locations
            self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Screenshot settings
        if "SCREENSHOT_WIDTH" in os.environ:
            self.screenshot.default_width = int(os.environ["SCREENSHOT_WIDTH"])
        if "SCREENSHOT_HEIGHT" in os.environ:
            self.screenshot.default_height = int(os.environ["SCREENSHOT_HEIGHT"])
        if "PAGE_LOAD_TIMEOUT" in os.environ:
            self.screenshot.page_load_timeout = int(os.environ["PAGE_LOAD_TIMEOUT"])
        if "DYNAMIC_CONTENT_WAIT" in os.environ:
            self.screenshot.dynamic_content_wait = int(os.environ["DYNAMIC_CONTENT_WAIT"])
        
        # AI settings
        if "AWS_DEFAULT_REGION" in os.environ:
            self.ai.default_aws_region = os.environ["AWS_DEFAULT_REGION"]
        if "MODEL_CONFIG_FILE" in os.environ:
            self.ai.default_model_config_file = os.environ["MODEL_CONFIG_FILE"]
        if "MAX_TOKENS" in os.environ:
            self.ai.max_tokens = int(os.environ["MAX_TOKENS"])
        
        # Storage settings
        if "SCREENSHOTS_DIR" in os.environ:
            self.storage.default_screenshots_dir = os.environ["SCREENSHOTS_DIR"]
        if "LOGS_DIR" in os.environ:
            self.storage.default_logs_dir = os.environ["LOGS_DIR"]
    
    def load_from_file(self, config_file: str):
        """
        Load configuration from a JSON file
        
        Args:
            config_file: Path to configuration file
        """
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Update configuration sections
            if "screenshot" in config_data:
                self._update_config_section(self.screenshot, config_data["screenshot"])
            if "image_tiling" in config_data:
                self._update_config_section(self.image_tiling, config_data["image_tiling"])
            if "ai" in config_data:
                self._update_config_section(self.ai, config_data["ai"])
            if "storage" in config_data:
                self._update_config_section(self.storage, config_data["storage"])
            if "performance" in config_data:
                self._update_config_section(self.performance, config_data["performance"])
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {config_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration file {config_file}: {e}")
    
    def _update_config_section(self, config_obj, config_data: Dict[str, Any]):
        """Update a configuration section with data from file"""
        for key, value in config_data.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
    
    def save_to_file(self, config_file: str):
        """
        Save current configuration to a JSON file
        
        Args:
            config_file: Path where to save configuration
        """
        config_data = {
            "screenshot": asdict(self.screenshot),
            "image_tiling": asdict(self.image_tiling),
            "ai": asdict(self.ai),
            "storage": asdict(self.storage),
            "performance": asdict(self.performance),
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_screenshot_defaults(self) -> Dict[str, Any]:
        """Get screenshot-related default values for CLI arguments"""
        return {
            "width": self.screenshot.default_width,
            "height": self.screenshot.default_height,
            "storage_dir": self.storage.default_screenshots_dir,
            "aws_region": self.ai.default_aws_region,
            "config": self.ai.default_model_config_file
        }
    
    def get_tiling_settings(self, image_width: int, image_height: int) -> Dict[str, int]:
        """
        Get optimal tiling settings for given image dimensions
        
        Args:
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            Dictionary with tile_height and overlap values
        """
        if image_height <= self.image_tiling.max_height_before_tiling:
            return {"tile_height": image_height, "overlap": 0}
        elif image_height <= self.image_tiling.medium_image_threshold:
            return {
                "tile_height": self.image_tiling.medium_tile_height,
                "overlap": self.image_tiling.medium_overlap
            }
        else:
            return {
                "tile_height": self.image_tiling.default_tile_height,
                "overlap": self.image_tiling.default_overlap
            }


# Global configuration instance
_global_config: Optional[AppConfig] = None


def get_config(config_file: Optional[str] = None, force_reload: bool = False) -> AppConfig:
    """
    Get the global configuration instance
    
    Args:
        config_file: Optional custom configuration file
        force_reload: Force reloading configuration
        
    Returns:
        AppConfig instance
    """
    global _global_config
    
    if _global_config is None or force_reload:
        _global_config = AppConfig(config_file)
    
    return _global_config


def create_sample_config(output_file: str = "app_config.json"):
    """
    Create a sample configuration file with all available settings
    
    Args:
        output_file: Where to save the sample configuration
    """
    sample_config = AppConfig()
    sample_config.save_to_file(output_file)
    print(f"Sample configuration created: {output_file}")


if __name__ == "__main__":
    # CLI for configuration management
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration management utility")
    parser.add_argument("--create-sample", action="store_true", 
                       help="Create a sample configuration file")
    parser.add_argument("--output", default="app_config.json",
                       help="Output file for sample configuration")
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_config(args.output)
    else:
        # Show current configuration
        config = get_config()
        print("Current Configuration:")
        print(f"  Screenshot: {config.screenshot}")
        print(f"  AI: {config.ai}")
        print(f"  Storage: {config.storage}") 