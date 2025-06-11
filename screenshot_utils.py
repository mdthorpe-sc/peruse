#!/usr/bin/env python3
"""
Shared screenshot utilities for both screenshot_tool.py and screenshot_monitor.py

This module contains common functionality to avoid code duplication between
the simple screenshot tool and the advanced monitoring tool.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Import logging framework
from logging_config import get_logger

# Import centralized configuration
from config import get_config, StringConstants

try:
    from playwright.async_api import async_playwright
except ImportError:
    logger = get_logger("screenshot_utils")
    logger.user_error("Playwright is not installed.")
    logger.user_info("Please run: pip install playwright")
    logger.user_info("Then run: playwright install")
    sys.exit(1)


class ScreenshotResult:
    """Result object for screenshot operations"""
    
    def __init__(self, success: bool, output_path: str = None, error: str = None):
        self.success = success
        self.output_path = output_path
        self.error = error
    
    def __bool__(self):
        return self.success


def sanitize_url_for_filename(url: str) -> str:
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
    
    return safe_name


def sanitize_url_for_storage_name(url: str) -> str:
    """Convert URL to a safe name for storage (used by monitor)"""
    # This is the same logic as sanitize_url_for_filename but with a different name
    # to maintain compatibility with existing monitor code
    return sanitize_url_for_filename(url)


def normalize_url(url: str) -> str:
    """Ensure URL has proper protocol prefix"""
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url


async def take_screenshot_core(
    url: str, 
    output_path: str, 
    viewport_width: int = None, 
    viewport_height: int = None,
    verbose: bool = True
) -> ScreenshotResult:
    """
    Core screenshot functionality shared between tools
    
    Args:
        url: URL to screenshot
        output_path: Path where to save the screenshot
        viewport_width: Browser viewport width (uses config default if None)
        viewport_height: Browser viewport height (uses config default if None)
        verbose: Whether to print status messages
    
    Returns:
        ScreenshotResult object with success status and details
    """
    logger = get_logger("screenshot_utils")
    config = get_config()
    
    # Use configuration defaults if not specified
    if viewport_width is None:
        viewport_width = config.screenshot.default_width
    if viewport_height is None:
        viewport_height = config.screenshot.default_height
    
    if verbose:
        logger.user_info(StringConstants.INFO_MESSAGES["taking_screenshot"].format(url=url))
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            
            try:
                page = await browser.new_page(viewport={
                    'width': viewport_width, 
                    'height': viewport_height
                })
                
                # Navigate with timeout and networkidle handling
                try:
                    await page.goto(url, wait_until='networkidle', timeout=config.screenshot.page_load_timeout)
                except Exception as e:
                    if verbose:
                        logger.user_warning(StringConstants.INFO_MESSAGES["networkidle_failed"].format(error=e))
                    # Try to continue anyway
                    await page.goto(url, timeout=config.screenshot.page_load_timeout)
                
                # Wait for dynamic content
                await page.wait_for_timeout(config.screenshot.dynamic_content_wait)
                
                # Take screenshot
                await page.screenshot(path=output_path, full_page=True)
                
                if verbose:
                    logger.user_success(StringConstants.SUCCESS_MESSAGES["screenshot_saved"].format(path=output_path))
                
                return ScreenshotResult(success=True, output_path=output_path)
                
            finally:
                await browser.close()
                
    except Exception as e:
        error_msg = f"Error taking screenshot: {e}"
        if verbose:
            logger.user_error(error_msg)
        return ScreenshotResult(success=False, error=error_msg)


async def take_screenshot_simple(
    url: str, 
    output_path: str, 
    viewport_width: int = None, 
    viewport_height: int = None
):
    """
    Simple screenshot function for basic use cases (screenshot_tool.py)
    Raises exceptions on failure for backward compatibility
    """
    result = await take_screenshot_core(url, output_path, viewport_width, viewport_height)
    
    if not result.success:
        raise Exception(result.error)


async def take_screenshot_with_result(
    url: str, 
    output_path: str, 
    viewport_width: int = None, 
    viewport_height: int = None,
    verbose: bool = True
) -> bool:
    """
    Screenshot function that returns boolean success (screenshot_monitor.py)
    """
    result = await take_screenshot_core(url, output_path, viewport_width, viewport_height, verbose)
    return result.success


def get_default_filename_for_url(url: str) -> str:
    """Generate a default filename for a URL"""
    config = get_config()
    safe_name = sanitize_url_for_filename(url)
    return f"{safe_name}{config.screenshot.default_extension}"


def ensure_png_extension(path: str) -> str:
    """Ensure a path ends with .png extension"""
    config = get_config()
    extension = config.screenshot.default_extension
    if not path.lower().endswith(extension.lower()):
        return path + extension
    return path


def validate_output_file(output_path: str, allow_overwrite: bool = False) -> bool:
    """
    Validate output file path and handle overwrite confirmation
    
    Args:
        output_path: Path to check
        allow_overwrite: If True, skip confirmation prompt
    
    Returns:
        True if file can be written, False if user cancels
    """
    if Path(output_path).exists() and not allow_overwrite:
        try:
            response = input(f"File '{output_path}' already exists. Overwrite? (y/N): ")
            return response.lower() in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            return False
    return True 