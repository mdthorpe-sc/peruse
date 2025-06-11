#!/usr/bin/env python3
"""
AI-Powered Screenshot Monitoring Tool

This tool captures website screenshots and uses Amazon Bedrock's Claude models
to intelligently detect and analyze changes for deployment monitoring.

For development context and session history, see: DEVELOPMENT_CONTEXT.md
For optimization roadmap, see: OPTIMIZATIONS.md

Usage: 
  python screenshot_monitor.py baseline <URL> [--name <name>] [--model <model>]
  python screenshot_monitor.py compare <URL> [--name <name>] [--model <model>]
  python screenshot_monitor.py list
  python screenshot_monitor.py list-models
"""

import argparse
import asyncio
import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import re
import uuid

# Import logging framework
from logging_config import get_logger

try:
    from playwright.async_api import async_playwright
except ImportError:
    logger = get_logger("screenshot_monitor")
    logger.user_error("Playwright is not installed.")
    logger.user_info("Please run: pip install playwright")
    logger.user_info("Then run: playwright install")
    sys.exit(1)

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    logger = get_logger("screenshot_monitor") 
    logger.user_error("boto3 is not installed.")
    logger.user_info("Please run: pip install boto3")
    sys.exit(1)

# Import shared screenshot utilities
from screenshot_utils import (
    take_screenshot_with_result,
    sanitize_url_for_storage_name,
    normalize_url
)

# Import image tiling functionality
from image_tiling import (
    needs_tiling,
    tile_image,
    analyze_tiled_image,
    cleanup_tiles,
    get_image_dimensions
)


class ScreenshotMonitor:
    # Class-level cache for model configuration
    _config_cache = {}
    _config_file_timestamps = {}
    
    # Cache the large prompt template as a class constant
    # This avoids reconstructing 500+ character string on every AI call
    _ANALYSIS_PROMPT_TEMPLATE = """You are a website monitoring expert analyzing screenshots for changes. I will provide you with two screenshots of the same website URL: {url}

The first image is the BASELINE (reference) screenshot.
The second image is the CURRENT screenshot taken more recently.

Please analyze these screenshots and provide a detailed comparison report in the following JSON format:

{{
    "has_changes": true/false,
    "severity": "none|minor|moderate|major|critical",
    "summary": "Brief summary of changes found",
    "changes_detected": [
        {{
            "type": "layout|content|styling|functionality|error|availability",
            "description": "Detailed description of the change",
            "location": "Where on the page this change occurs",
            "impact": "Potential impact of this change"
        }}
    ],
    "availability_status": "available|partially_available|unavailable|error",
    "recommendations": ["List of recommended actions if any issues found"]
}}

Focus on:
- Layout changes (elements moved, resized, disappeared)
- Content changes (text differences, images changed)
- Error messages or broken elements
- Overall site availability and functionality
- Visual styling changes
- Any elements that appear broken or missing

Be thorough but practical - highlight changes that would matter for deployment monitoring."""
    
    def __init__(self, storage_dir: str = "screenshots", aws_region: str = "us-east-1", model_name: str = None, config_file: str = "models.json"):
        # Initialize logger
        self.logger = get_logger("screenshot_monitor")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_file = self.storage_dir / "metadata.json"
        self.aws_region = aws_region
        self.config_file = config_file
        
        # Load model configurations from JSON file
        self.model_config = self.load_model_config()
        
        # Use default model if none specified
        if model_name is None:
            model_name = self.model_config.get("default_model", "claude-4-sonnet")
        
        self.model_name = model_name
        
        # Validate and set model IDs
        available_models = self.model_config.get("models", {})
        if model_name not in available_models:
            available = list(available_models.keys())
            raise ValueError(f"Unknown model '{model_name}'. Available models: {available}")
        
        model_details = available_models[model_name]
        self.model_ids = [
            model_details["inference_profile"],  # Inference profile (preferred)
            model_details["direct"]              # Direct model (fallback)
        ]
        self.model_description = model_details["description"]
        
        # Initialize Bedrock client
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name=aws_region)
        except NoCredentialsError:
            self.logger.user_error("AWS credentials not found.")
            self.logger.user_info("Please configure AWS credentials using:")
            self.logger.user_info("  aws configure")
            self.logger.user_info("  or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            sys.exit(1)
    
    def load_model_config(self) -> dict:
        """Load model configuration from JSON file with caching"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Model configuration file '{self.config_file}' not found. "
                f"Please ensure the file exists in the current directory."
            )
        
        try:
            # Get file modification time
            file_mtime = config_path.stat().st_mtime
            
            # Check if we have a cached version that's still valid
            if (self.config_file in self._config_cache and 
                self.config_file in self._config_file_timestamps and
                self._config_file_timestamps[self.config_file] >= file_mtime):
                # Use cached configuration
                return self._config_cache[self.config_file]
            
            # Need to load from file
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate basic structure
            if "models" not in config:
                raise ValueError("Configuration file must contain a 'models' section")
            
            if not isinstance(config["models"], dict):
                raise ValueError("'models' section must be a dictionary")
            
            # Validate each model has required fields
            for model_name, model_data in config["models"].items():
                required_fields = ["inference_profile", "direct", "description"]
                for field in required_fields:
                    if field not in model_data:
                        raise ValueError(f"Model '{model_name}' missing required field: '{field}'")
            
            # Cache the configuration
            self._config_cache[self.config_file] = config
            self._config_file_timestamps[self.config_file] = file_mtime
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file '{self.config_file}': {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration file '{self.config_file}': {e}")
    
    def load_metadata(self) -> dict:
        """Load metadata about stored screenshots"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_metadata(self, metadata: dict):
        """Save metadata about stored screenshots"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def sanitize_name(self, url: str) -> str:
        """Convert URL to a safe name for storage"""
        return sanitize_url_for_storage_name(url)
    
    async def take_screenshot(self, url: str, output_path: str, viewport_width: int = 1920, viewport_height: int = 1080) -> bool:
        """Take a screenshot of the given URL"""
        return await take_screenshot_with_result(url, output_path, viewport_width, viewport_height)
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for Bedrock API"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def compare_with_claude(self, baseline_path: str, current_path: str, url: str) -> dict:
        """Use Claude via Bedrock Converse API to compare screenshots"""
        self.logger.operation_start(f"Analyzing screenshots with {self.model_name} ({self.model_description})")
        
        try:
            # Encode images
            baseline_b64 = self.encode_image_to_base64(baseline_path)
            current_b64 = self.encode_image_to_base64(current_path)
            
            # Prepare the prompt
            prompt = self._ANALYSIS_PROMPT_TEMPLATE.format(url=url)

            # Try different model IDs until one works
            response = None
            last_error = None
            
            for model_id in self.model_ids:
                try:
                    self.logger.debug(f"Trying model: {model_id}")
                    response = self.bedrock.converse(
                        modelId=model_id,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "text": prompt
                                    },
                                    {
                                        "image": {
                                            "format": "png",
                                            "source": {
                                                "bytes": base64.b64decode(baseline_b64)
                                            }
                                        }
                                    },
                                    {
                                        "image": {
                                            "format": "png", 
                                            "source": {
                                                "bytes": base64.b64decode(current_b64)
                                            }
                                        }
                                    }
                                ]
                            }
                        ],
                        inferenceConfig={
                            "maxTokens": 4000,
                            "temperature": 0.1,
                            "topP": 0.9
                        }
                    )
                    self.logger.user_success(f"Successfully using model: {model_id}")
                    break
                except ClientError as e:
                    last_error = e
                    error_code = e.response['Error']['Code']
                    self.logger.user_error(f"Model {model_id} failed: {error_code}")
                    continue
            
            if response is None:
                # All models failed, raise the last error
                raise last_error
            
            # Parse response from Converse API
            claude_response = response['output']['message']['content'][0]['text']
            
            # Try to extract JSON from Claude's response
            try:
                # Find JSON in the response
                json_start = claude_response.find('{')
                json_end = claude_response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    analysis = json.loads(claude_response[json_start:json_end])
                else:
                    # Fallback if no JSON found
                    analysis = {
                        "has_changes": True,
                        "severity": "unknown",
                        "summary": "Analysis completed but format parsing failed",
                        "raw_response": claude_response
                    }
            except json.JSONDecodeError:
                analysis = {
                    "has_changes": True,
                    "severity": "unknown", 
                    "summary": "Analysis completed but JSON parsing failed",
                    "raw_response": claude_response
                }
            
            return analysis
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ValidationException':
                self.logger.user_error("Invalid request to Bedrock. Check your image format and size.")
                self.logger.user_info(f"Tip: Make sure you have access to {self.model_name} in your AWS region.")
            elif error_code == 'AccessDeniedException':
                self.logger.user_error("Access denied to Bedrock. Check your AWS permissions.")
                self.logger.user_info("Tip: Request access to Claude models in Bedrock console: Model access > Request model access")
            elif error_code == 'ResourceNotFoundException':
                self.logger.user_error("Model not found. The inference profile may not be available in your region.")
                self.logger.user_info("Tip: Try a different AWS region or check model availability.")
            else:
                self.logger.user_error(f"AWS Error: {e}")
            return {"error": str(e)}
        except Exception as e:
            self.logger.user_error(f"Error during comparison: {e}")
            return {"error": str(e)}
    
    def compare_with_claude_auto_tiling(self, baseline_path: str, current_path: str, url: str) -> dict:
        """
        Compare screenshots with automatic tiling for large images.
        
        This method automatically detects if images need tiling due to size constraints
        and handles the tiling workflow transparently.
        
        Args:
            baseline_path: Path to baseline screenshot
            current_path: Path to current screenshot  
            url: URL being analyzed
            
        Returns:
            Analysis results (either from single image or combined tile analysis)
        """
        baseline_tiles = []
        current_tiles = []
        
        try:
            # Check if either image needs tiling
            baseline_needs_tiling = needs_tiling(baseline_path)
            current_needs_tiling = needs_tiling(current_path)
            
            if baseline_needs_tiling or current_needs_tiling:
                # At least one image needs tiling - tile both for consistency
                baseline_dims = get_image_dimensions(baseline_path)
                current_dims = get_image_dimensions(current_path)
                
                self.logger.user_info(f"Large images detected:")
                self.logger.user_info(f"  Baseline: {baseline_dims[0]}x{baseline_dims[1]}")  
                self.logger.user_info(f"  Current: {current_dims[0]}x{current_dims[1]}")
                self.logger.user_info("🔧 Using image tiling for analysis...")
                
                # Tile both images
                baseline_tiles = tile_image(baseline_path, tile_height=3000, overlap=200)
                current_tiles = tile_image(current_path, tile_height=3000, overlap=200)
                
                self.logger.user_info(f"Created {len(baseline_tiles)} baseline tiles and {len(current_tiles)} current tiles")
                
                # Analyze tiled images
                analysis = analyze_tiled_image(baseline_tiles, current_tiles, url, self)
                
                # Add tiling metadata to analysis
                analysis["tiling_used"] = True
                analysis["baseline_dimensions"] = baseline_dims
                analysis["current_dimensions"] = current_dims
                analysis["tile_count"] = len(baseline_tiles)
                
            else:
                # Images are small enough for direct comparison
                baseline_dims = get_image_dimensions(baseline_path)
                current_dims = get_image_dimensions(current_path)
                
                self.logger.debug(f"Images within size limits: {baseline_dims[0]}x{baseline_dims[1]} and {current_dims[0]}x{current_dims[1]}")
                
                # Use existing single-image comparison
                analysis = self.compare_with_claude(baseline_path, current_path, url)
                
                # Add metadata
                analysis["tiling_used"] = False
                analysis["baseline_dimensions"] = baseline_dims
                analysis["current_dimensions"] = current_dims
            
            return analysis
            
        except Exception as e:
            self.logger.user_error(f"Error during tiling analysis: {e}")
            return {"error": str(e), "tiling_used": False}
            
        finally:
            # Always clean up temporary tile files
            if baseline_tiles:
                cleanup_tiles(baseline_tiles)
            if current_tiles:
                cleanup_tiles(current_tiles)
    
    async def store_baseline(self, url: str, name: str = None, viewport_width: int = 1920, viewport_height: int = 1080):
        """Store a baseline screenshot"""
        if not name:
            name = self.sanitize_name(url)
        
        timestamp = datetime.now().isoformat()
        screenshot_id = str(uuid.uuid4())[:8]
        filename = f"{name}_baseline_{screenshot_id}.png"
        screenshot_path = self.storage_dir / filename
        
        # Take screenshot
        success = await self.take_screenshot(url, str(screenshot_path), viewport_width, viewport_height)
        
        if success:
            # Update metadata
            metadata = self.load_metadata()
            metadata[name] = {
                "url": url,
                "baseline_file": filename,
                "baseline_path": str(screenshot_path),
                "timestamp": timestamp,
                "viewport": {"width": viewport_width, "height": viewport_height}
            }
            self.save_metadata(metadata)
            
            self.logger.user_success(f"Baseline stored for '{name}'")
            self.logger.user_info(f"   URL: {url}")
            self.logger.user_info(f"   File: {filename}")
            self.logger.user_info(f"   Timestamp: {timestamp}")
        else:
            self.logger.user_error(f"Failed to store baseline for '{name}'")
    
    async def compare_with_baseline(self, url: str, name: str = None, baseline_file: str = None):
        """Compare current screenshot with stored baseline"""
        if not name:
            name = self.sanitize_name(url)
        
        metadata = self.load_metadata()
        
        # Find baseline
        baseline_path = None
        if baseline_file:
            baseline_path = self.storage_dir / baseline_file
            if not baseline_path.exists():
                self.logger.user_error(f"Baseline file not found: {baseline_file}")
                return
        elif name in metadata:
            baseline_path = Path(metadata[name]["baseline_path"])
            if not baseline_path.exists():
                self.logger.user_error(f"Baseline file not found: {baseline_path}")
                return
        else:
            self.logger.user_error(f"No baseline found for '{name}'. Available baselines:")
            for key in metadata.keys():
                self.logger.user_info(f"   - {key}")
            self.logger.user_info("\nTo create a baseline for this URL, run:")
            self.logger.user_info(f"   python screenshot_monitor.py baseline {url} --name {name}")
            return
        
        # Take current screenshot
        timestamp = datetime.now().isoformat()
        current_filename = f"{name}_current_{int(time.time())}.png"
        current_path = self.storage_dir / current_filename
        
        self.logger.operation_start(f"Comparing {url} with baseline")
        success = await self.take_screenshot(url, str(current_path))
        
        if not success:
            self.logger.user_error("Failed to take current screenshot")
            return
        
        # Compare with Claude (with automatic tiling for large images)
        analysis = self.compare_with_claude_auto_tiling(str(baseline_path), str(current_path), url)
        
        # Generate report
        self.generate_report(analysis, name, url, str(baseline_path), str(current_path), timestamp)
    
    def generate_report(self, analysis: dict, name: str, url: str, baseline_path: str, current_path: str, timestamp: str):
        """Generate and display comparison report"""
        self.logger.report_section("CHANGE DETECTION REPORT")
        self.logger.report_item("Site", name)
        self.logger.report_item("URL", url)
        self.logger.report_item("Timestamp", timestamp)
        self.logger.report_item("Baseline", Path(baseline_path).name)
        self.logger.report_item("Current", Path(current_path).name)
        self.logger.report_subsection("")
        
        if "error" in analysis:
            self.logger.user_error(f"Analysis Error: {analysis['error']}")
            return
        
        # Status indicators
        has_changes = analysis.get('has_changes', False)
        severity = analysis.get('severity', 'unknown')
        availability = analysis.get('availability_status', 'unknown')
        
        self.logger.report_item("Changes Detected", '🔴 YES' if has_changes else '🟢 NO')
        self.logger.report_item("Severity", f"{self.get_severity_emoji(severity)} {severity.upper()}")
        self.logger.report_item("Availability", f"{self.get_availability_emoji(availability)} {availability.upper()}")
        
        # Show tiling information if used
        if analysis.get("tiling_used"):
            baseline_dims = analysis.get("baseline_dimensions", (0, 0))
            current_dims = analysis.get("current_dimensions", (0, 0))
            tile_count = analysis.get("tile_count", 0)
            self.logger.report_item("Analysis Method", f"🔧 Image Tiling ({tile_count} tiles)")
            self.logger.report_item("Image Dimensions", f"Baseline: {baseline_dims[0]}x{baseline_dims[1]}, Current: {current_dims[0]}x{current_dims[1]}")
        else:
            baseline_dims = analysis.get("baseline_dimensions", (0, 0))
            current_dims = analysis.get("current_dimensions", (0, 0))
            self.logger.report_item("Analysis Method", "📷 Single Image")
            self.logger.report_item("Image Dimensions", f"Baseline: {baseline_dims[0]}x{baseline_dims[1]}, Current: {current_dims[0]}x{current_dims[1]}")
        
        if analysis.get('summary'):
            self.logger.user_info(f"\n📝 Summary:")
            self.logger.user_info(f"   {analysis['summary']}")
        
        # Detailed changes
        if analysis.get('changes_detected'):
            self.logger.user_info(f"\n🔍 Changes Found:")
            for i, change in enumerate(analysis['changes_detected'], 1):
                self.logger.user_info(f"   {i}. Type: {change.get('type', 'unknown')}")
                self.logger.user_info(f"      Description: {change.get('description', 'N/A')}")
                self.logger.user_info(f"      Location: {change.get('location', 'N/A')}")
                self.logger.user_info(f"      Impact: {change.get('impact', 'N/A')}")
                self.logger.user_info("")
        
        # Recommendations
        if analysis.get('recommendations'):
            self.logger.user_info(f"💡 Recommendations:")
            for rec in analysis['recommendations']:
                self.logger.user_info(f"   • {rec}")
        
        # Save detailed report
        report_file = self.storage_dir / f"{name}_report_{int(time.time())}.json"
        full_report = {
            "metadata": {
                "name": name,
                "url": url,
                "timestamp": timestamp,
                "baseline_file": Path(baseline_path).name,
                "current_file": Path(current_path).name
            },
            "analysis": analysis
        }
        
        with open(report_file, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        self.logger.user_info(f"\n📄 Detailed report saved: {report_file.name}")
        self.logger.user_info("="*60)
    
    def get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level"""
        mapping = {
            'none': '🟢',
            'minor': '🟡', 
            'moderate': '🟠',
            'major': '🔴',
            'critical': '🚨'
        }
        return mapping.get(severity.lower(), '❓')
    
    def get_availability_emoji(self, availability: str) -> str:
        """Get emoji for availability status"""
        mapping = {
            'available': '🟢',
            'partially_available': '🟡',
            'unavailable': '🔴',
            'error': '🚨'
        }
        return mapping.get(availability.lower(), '❓')
    
    def list_baselines(self):
        """List all stored baselines"""
        metadata = self.load_metadata()
        
        if not metadata:
            self.logger.user_info("No baselines stored yet.")
            return
        
        self.logger.user_info("\n📁 Stored Baselines:")
        self.logger.user_info("-" * 60)
        for name, info in metadata.items():
            self.logger.user_info(f"Name: {name}")
            self.logger.user_info(f"URL: {info['url']}")
            self.logger.user_info(f"File: {info['baseline_file']}")
            self.logger.user_info(f"Created: {info['timestamp']}")
            self.logger.user_info(f"Viewport: {info['viewport']['width']}x{info['viewport']['height']}")
            self.logger.user_info("-" * 40)
    
    @staticmethod
    def list_available_models(config_file: str = "models.json"):
        """List all available Claude models from configuration file"""
        logger = get_logger("screenshot_monitor")
        try:
            config_path = Path(config_file)
            
            if not config_path.exists():
                logger.user_error(f"Model configuration file '{config_file}' not found.")
                return
            
            # Get file modification time
            file_mtime = config_path.stat().st_mtime
            
            # Check if we have a cached version that's still valid
            if (config_file in ScreenshotMonitor._config_cache and 
                config_file in ScreenshotMonitor._config_file_timestamps and
                ScreenshotMonitor._config_file_timestamps[config_file] >= file_mtime):
                # Use cached configuration
                config = ScreenshotMonitor._config_cache[config_file]
            else:
                # Load from file and cache it
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Cache the configuration
                ScreenshotMonitor._config_cache[config_file] = config
                ScreenshotMonitor._config_file_timestamps[config_file] = file_mtime
            
            models = config.get("models", {})
            default_model = config.get("default_model", "N/A")
            metadata = config.get("metadata", {})
            
            logger.user_info("\n🤖 Available Claude Models:")
            logger.user_info("=" * 80)
            
            if metadata:
                logger.user_info(f"Configuration Version: {metadata.get('version', 'Unknown')}")
                logger.user_info(f"Last Updated: {metadata.get('last_updated', 'Unknown')}")
                logger.user_info(f"Default Model: {default_model}")
                logger.user_info("-" * 80)
            
            for model_name, model_config in models.items():
                logger.user_info(f"Model: {model_name}")
                logger.user_info(f"Description: {model_config.get('description', 'N/A')}")
                
                # Show additional metadata if available
                if 'speed' in model_config:
                    logger.user_info(f"Speed: {model_config['speed'].title()}")
                if 'cost' in model_config:
                    logger.user_info(f"Cost: {model_config['cost'].title()}")
                if 'quality' in model_config:
                    logger.user_info(f"Quality: {model_config['quality'].title()}")
                
                logger.user_info(f"Inference Profile: {model_config.get('inference_profile', 'N/A')}")
                logger.user_info(f"Direct Model: {model_config.get('direct', 'N/A')}")
                logger.user_info("-" * 60)
            
        except json.JSONDecodeError as e:
            logger.user_error(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            logger.user_error(f"Error reading configuration file: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="Website Screenshot Monitoring with AI-Powered Change Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Store a baseline screenshot
  python screenshot_monitor.py baseline https://example.com --name mysite
  
  # Compare current with baseline using Claude 3.5 Sonnet
  python screenshot_monitor.py compare https://example.com --name mysite --model claude-3.5-sonnet
  
  # List all stored baselines
  python screenshot_monitor.py list
  
  # List available Claude models
  python screenshot_monitor.py list-models
  
  # Use custom model configuration file
  python screenshot_monitor.py compare https://example.com --config my-models.json
        """
    )
    
    parser.add_argument('command', choices=['baseline', 'compare', 'list', 'list-models'], 
                       help='Command to execute')
    parser.add_argument('url', nargs='?', help='URL to process')
    parser.add_argument('--name', help='Name for the baseline (auto-generated if not provided)')
    parser.add_argument('--baseline-file', help='Specific baseline file to compare against')
    parser.add_argument('--width', type=int, default=1920, help='Viewport width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Viewport height (default: 1080)')
    parser.add_argument('--storage-dir', default='screenshots', help='Directory to store screenshots')
    parser.add_argument('--aws-region', default='us-east-1', help='AWS region for Bedrock')
    parser.add_argument('--model', 
                       help='Claude model to use (default from config file). Use list-models to see options')
    parser.add_argument('--config', default='models.json',
                       help='Path to model configuration file (default: models.json)')
    
    args = parser.parse_args()
    
    # Handle list-models command (no monitor needed)
    if args.command == 'list-models':
        ScreenshotMonitor.list_available_models(args.config)
        return
    
    # Create monitor with specified model
    try:
        monitor = ScreenshotMonitor(args.storage_dir, args.aws_region, args.model, args.config)
    except (ValueError, FileNotFoundError) as e:
        logger = get_logger("screenshot_monitor")
        logger.user_error(f"{e}")
        logger.user_info(f"Use 'python screenshot_monitor.py list-models --config {args.config}' to see available models")
        sys.exit(1)
    
    if args.command == 'list':
        monitor.list_baselines()
        return
    
    if not args.url:
        logger = get_logger("screenshot_monitor")
        logger.user_error("URL is required for baseline and compare commands")
        sys.exit(1)
    
    # Validate and normalize URL
    url = normalize_url(args.url)
    if url != args.url:
        logger = get_logger("screenshot_monitor")
        logger.user_info(f"Adding https:// to URL: {url}")
    
    try:
        if args.command == 'baseline':
            await monitor.store_baseline(url, args.name, args.width, args.height)
        elif args.command == 'compare':
            await monitor.compare_with_baseline(url, args.name, args.baseline_file)
    
    except KeyboardInterrupt:
        logger = get_logger("screenshot_monitor")
        logger.user_info("\nCancelled by user.")
    except Exception as e:
        logger = get_logger("screenshot_monitor")
        logger.user_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 