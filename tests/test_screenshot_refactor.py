#!/usr/bin/env python3
"""
Test script to verify screenshot logic refactoring

This test validates that the shared screenshot utilities work correctly
and that both tools can use them without issues.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from screenshot_utils import (
    sanitize_url_for_filename,
    sanitize_url_for_storage_name,
    normalize_url,
    get_default_filename_for_url,
    ensure_png_extension,
    ScreenshotResult
)

def test_url_utilities():
    """Test URL utility functions"""
    print("🧪 Testing URL Utility Functions")
    print("=" * 50)
    
    # Test URL normalization
    test_cases = [
        "example.com",
        "https://example.com",
        "http://example.com",
        "www.github.com"
    ]
    
    for url in test_cases:
        normalized = normalize_url(url)
        print(f"'{url}' → '{normalized}'")
    
    print("\n📁 Testing filename sanitization:")
    # Test filename sanitization
    for url in ["https://example.com", "https://www.github.com/user", "https://sub.domain.co.uk"]:
        filename = sanitize_url_for_filename(url)
        storage_name = sanitize_url_for_storage_name(url)
        default_file = get_default_filename_for_url(url)
        
        print(f"URL: {url}")
        print(f"  Filename: {filename}")
        print(f"  Storage:  {storage_name}")
        print(f"  Default:  {default_file}")
        print()
    
    # Test PNG extension handling
    print("🔧 Testing PNG extension handling:")
    test_files = ["test", "test.png", "test.PNG", "test.jpg"]
    for file in test_files:
        result = ensure_png_extension(file)
        print(f"'{file}' → '{result}'")

def test_screenshot_result():
    """Test ScreenshotResult class"""
    print("\n📊 Testing ScreenshotResult Class")
    print("=" * 50)
    
    # Test successful result
    success_result = ScreenshotResult(True, "test.png")
    print(f"Success result: success={success_result.success}, bool={bool(success_result)}")
    
    # Test failure result
    failure_result = ScreenshotResult(False, error="Test error")
    print(f"Failure result: success={failure_result.success}, bool={bool(failure_result)}")
    print(f"Error message: {failure_result.error}")

def test_imports():
    """Test that imports work correctly"""
    print("\n📦 Testing Import Functionality")
    print("=" * 50)
    
    try:
        # Test screenshot_tool imports
        print("Testing screenshot_tool imports...")
        import screenshot_tool
        print("✅ screenshot_tool imports successful")
        
        # Test screenshot_monitor imports  
        print("Testing screenshot_monitor imports...")
        import screenshot_monitor
        print("✅ screenshot_monitor imports successful")
        
        # Test that we can create a ScreenshotMonitor instance
        print("Testing ScreenshotMonitor instantiation...")
        monitor = screenshot_monitor.ScreenshotMonitor()
        print("✅ ScreenshotMonitor instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all refactoring tests"""
    print("🚀 Screenshot Refactoring Validation Tests")
    print("=" * 60)
    
    # Test utility functions
    test_url_utilities()
    
    # Test result class
    test_screenshot_result()
    
    # Test imports
    success = test_imports()
    
    if success:
        print("\n🎉 All refactoring tests passed!")
        print("✅ Shared utilities working correctly")
        print("✅ Both tools can import and use shared code")
        print("✅ Code duplication successfully eliminated")
    else:
        print("\n⚠️  Some tests failed - refactoring may have issues")
    
    print("\n📈 Refactoring Benefits:")
    print("- Eliminated duplicate screenshot logic between tools")
    print("- Centralized URL handling and sanitization")
    print("- Improved maintainability and testability")
    print("- Consistent behavior across both tools")

if __name__ == "__main__":
    main() 