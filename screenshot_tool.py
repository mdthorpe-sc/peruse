#!/usr/bin/env python3
"""
Simple URL Screenshot Tool
Usage: python screenshot_tool.py <URL> [output_filename]
"""

import argparse
import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse
import re

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: Playwright is not installed.")
    print("Please run: pip install playwright")
    print("Then run: playwright install")
    sys.exit(1)


def sanitize_filename(url: str) -> str:
    """Convert URL to a safe filename"""
    # Parse the URL to get the domain
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    
    # Remove www. prefix if present
    domain = re.sub(r'^www\.', '', domain)
    
    # Replace unsafe characters with underscores
    safe_name = re.sub(r'[^\w\-.]', '_', domain)
    
    # Remove multiple consecutive underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    
    return f"{safe_name}.png"


async def take_screenshot(url: str, output_path: str, viewport_width: int = 1920, viewport_height: int = 1080):
    """Take a screenshot of the given URL"""
    print(f"Taking screenshot of: {url}")
    
    async with async_playwright() as p:
        # Launch browser (headless by default)
        browser = await p.chromium.launch()
        
        try:
            # Create a new page with specified viewport
            page = await browser.new_page(viewport={'width': viewport_width, 'height': viewport_height})
            
            # Navigate to the URL with a reasonable timeout
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
            except Exception as e:
                print(f"Warning: Failed to wait for networkidle: {e}")
                # Try to continue anyway
                await page.goto(url, timeout=30000)
            
            # Wait a bit for any dynamic content
            await page.wait_for_timeout(2000)
            
            # Take screenshot
            await page.screenshot(path=output_path, full_page=True)
            print(f"Screenshot saved to: {output_path}")
            
        finally:
            await browser.close()


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
    
    # Validate URL
    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"Adding https:// to URL: {url}")
    
    # Determine output filename
    if args.output:
        output_path = args.output
    else:
        output_path = sanitize_filename(url)
    
    # Ensure output path has .png extension
    if not output_path.lower().endswith('.png'):
        output_path += '.png'
    
    # Check if output file already exists
    if Path(output_path).exists():
        response = input(f"File '{output_path}' already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return
    
    try:
        # Run the screenshot function
        asyncio.run(take_screenshot(url, output_path, args.width, args.height))
    except KeyboardInterrupt:
        print("\nCancelled by user.")
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 