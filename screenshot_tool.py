#!/usr/bin/env python3
"""
Simple URL Screenshot Tool
Usage: python screenshot_tool.py <URL> [output_filename]
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Import logging framework
from logging_config import get_logger

# Import shared screenshot utilities
from screenshot_utils import (
    take_screenshot_simple,
    normalize_url,
    get_default_filename_for_url,
    ensure_png_extension,
    validate_output_file
)

# Import centralized configuration
from config import get_config, StringConstants


# Removed duplicated functions - now using shared screenshot_utils module


def main():
    logger = get_logger("screenshot_tool")
    config = get_config()
    
    parser = argparse.ArgumentParser(
        description="Take a screenshot of a webpage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python screenshot_tool.py https://example.com
  python screenshot_tool.py https://google.com my_screenshot.png
  python screenshot_tool.py https://github.com --width 1280 --height 720
        """
    )
    
    parser.add_argument('url', help='URL to screenshot')
    parser.add_argument('output', nargs='?', help='Output filename (optional)')
    parser.add_argument('--width', type=int, default=config.screenshot.default_width, 
                       help=f'Viewport width (default: {config.screenshot.default_width})')
    parser.add_argument('--height', type=int, default=config.screenshot.default_height, 
                       help=f'Viewport height (default: {config.screenshot.default_height})')
    
    args = parser.parse_args()
    
    # Validate and normalize URL
    url = normalize_url(args.url)
    if url != args.url:
        logger.user_info(StringConstants.INFO_MESSAGES["url_normalized"].format(url=url))
    
    # Determine output filename
    if args.output:
        output_path = ensure_png_extension(args.output)
    else:
        output_path = get_default_filename_for_url(url)
    
    # Check if output file already exists and get user confirmation
    if not validate_output_file(output_path):
        logger.user_info(StringConstants.INFO_MESSAGES["cancelled"])
        return
    
    try:
        # Run the screenshot function using shared utilities
        asyncio.run(take_screenshot_simple(url, output_path, args.width, args.height))
    except KeyboardInterrupt:
        logger.user_info("\nCancelled by user.")
    except Exception as e:
        logger.user_error(f"Error taking screenshot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 