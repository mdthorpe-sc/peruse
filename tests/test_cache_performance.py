#!/usr/bin/env python3
"""
Test script to demonstrate model configuration loading performance

This test can be used to:
1. Measure baseline performance without caching
2. Test performance improvements when caching is implemented
3. Validate that caching doesn't break functionality
"""

import time
import json
import sys
from pathlib import Path

# Add parent directory to path to import screenshot_monitor
sys.path.append(str(Path(__file__).parent.parent))

try:
    from screenshot_monitor import ScreenshotMonitor
except ImportError:
    print("❌ Could not import ScreenshotMonitor")
    print("Make sure you're running this from the project root or tests directory")
    sys.exit(1)

def test_configuration_loading_performance():
    """Test the performance of configuration loading"""
    print("🧪 Testing Model Configuration Loading Performance")
    print("=" * 70)
    
    # Check if caching is implemented
    caching_enabled = hasattr(ScreenshotMonitor, '_config_cache')
    print(f"Caching Implementation: {'✅ Enabled' if caching_enabled else '❌ Not Implemented'}")
    
    if caching_enabled:
        # Clear any existing cache to start fresh
        ScreenshotMonitor._config_cache.clear()
        ScreenshotMonitor._config_file_timestamps.clear()
        print("Cache cleared for fresh test")
    
    print("\nTesting 10 consecutive configuration loads...")
    print("-" * 50)
    
    # Test loading configuration multiple times
    times = []
    for i in range(10):
        start_time = time.time()
        
        try:
            # Create a new instance (which loads config)
            monitor = ScreenshotMonitor()
            success = True
        except Exception as e:
            print(f"❌ Error creating ScreenshotMonitor: {e}")
            success = False
        
        end_time = time.time()
        load_time = (end_time - start_time) * 1000  # Convert to milliseconds
        times.append(load_time)
        
        status = "✅" if success else "❌"
        print(f"Load {i+1:2d}: {load_time:7.2f}ms {status}")
    
    print("\n📊 Performance Analysis:")
    print("=" * 50)
    
    if len(times) > 1:
        first_load = times[0]
        subsequent_loads = times[1:]
        avg_subsequent = sum(subsequent_loads) / len(subsequent_loads)
        
        print(f"First load:              {first_load:7.2f}ms")
        print(f"Average subsequent:      {avg_subsequent:7.2f}ms")
        print(f"Min subsequent:          {min(subsequent_loads):7.2f}ms")
        print(f"Max subsequent:          {max(subsequent_loads):7.2f}ms")
        
        if avg_subsequent > 0:
            improvement = first_load / avg_subsequent
            print(f"Performance ratio:       {improvement:7.1f}x")
            
            if improvement > 2.0:
                print("🚀 Significant performance improvement detected!")
            elif improvement > 1.5:
                print("⚡ Moderate performance improvement detected")
            else:
                print("📈 Minimal performance difference")
    
    # Test cache behavior if implemented
    if caching_enabled:
        print(f"\n💾 Cache Status:")
        print(f"Cached configurations: {len(ScreenshotMonitor._config_cache)}")
        cache_keys = list(ScreenshotMonitor._config_cache.keys())
        if cache_keys:
            print(f"Cache keys: {cache_keys}")
            for key in cache_keys:
                config = ScreenshotMonitor._config_cache[key]
                model_count = len(config.get('models', {}))
                print(f"  - {key}: {model_count} models cached")

def test_functionality_validation():
    """Validate that basic functionality still works"""
    print("\n🔍 Functionality Validation:")
    print("=" * 40)
    
    try:
        # Test instance creation
        monitor = ScreenshotMonitor()
        print("✅ ScreenshotMonitor instance created")
        
        # Test model configuration access
        config = monitor.model_config
        models = config.get('models', {})
        print(f"✅ Model configuration loaded: {len(models)} models")
        
        # Test model listing
        ScreenshotMonitor.list_available_models()
        print("✅ Model listing functionality works")
        
        # Test default model selection
        default_model = config.get('default_model', 'N/A')
        print(f"✅ Default model: {default_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Run all performance tests"""
    print("🚀 Screenshot Monitor Performance Test Suite")
    print("=" * 70)
    
    # Check if models.json exists
    models_file = Path("models.json")
    if not models_file.exists():
        print("❌ models.json not found in current directory")
        print("Please run this test from the project root directory")
        return
    
    print(f"📁 Using configuration file: {models_file.absolute()}")
    print(f"📏 Configuration file size: {models_file.stat().st_size} bytes")
    
    # Run performance test
    test_configuration_loading_performance()
    
    # Validate functionality
    if test_functionality_validation():
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some functionality tests failed")
    
    print("\n💡 Tips for optimization:")
    print("- Implement configuration caching to reduce file I/O")
    print("- Cache validation with file modification time tracking")
    print("- Consider lazy loading for AWS client initialization")

if __name__ == "__main__":
    main() 