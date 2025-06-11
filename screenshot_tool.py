#!/usr/bin/env python3
"""
Simple URL Screenshot Tool
Usage: python screenshot_tool.py <URL> [output_filename]
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Import shared screenshot utilities
from screenshot_utils import (
    take_screenshot_simple,
    normalize_url,
    get_default_filename_for_url,
    ensure_png_extension,
    validate_output_file
)


# Removed duplicated functions - now using shared screenshot_utils module


def main():
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
    parser.add_argument('--width', type=int, default=1920, help='Viewport width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Viewport height (default: 1080)')
    
    args = parser.parse_args()
    
    # Validate and normalize URL
    url = normalize_url(args.url)
    if url != args.url:
        print(f"Adding https:// to URL: {url}")
    
    # Determine output filename
    if args.output:
        output_path = ensure_png_extension(args.output)
    else:
        output_path = get_default_filename_for_url(url)
    
    # Check if output file already exists and get user confirmation
    if not validate_output_file(output_path):
        print("Cancelled.")
        return
    
    try:
        # Run the screenshot function using shared utilities
        asyncio.run(take_screenshot_simple(url, output_path, args.width, args.height))
    except KeyboardInterrupt:
        print("\nCancelled by user.")
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 