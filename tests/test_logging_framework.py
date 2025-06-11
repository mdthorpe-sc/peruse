#!/usr/bin/env python3
"""
Test the logging framework functionality.

This test validates that the logging framework works correctly and maintains
the same user experience while adding proper logging infrastructure.
"""

import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger, configure_logging


def test_basic_logging():
    """Test basic logging functionality"""
    print("🧪 Testing basic logging functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configure logging to use temp directory
        logger = get_logger("test_logger", log_dir=temp_dir)
        
        # Test that logging methods work without errors
        logger.user_info("Test info message")
        logger.user_success("Test success message") 
        logger.user_warning("Test warning message")
        logger.user_error("Test error message")
        
        # Check log file was created
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) > 0, "Log file should be created"
        
        # Check log file contains detailed logging
        log_content = log_files[0].read_text()
        assert "test_logger" in log_content
        assert "Test info message" in log_content
        assert "Test success message" in log_content
        
        print("✅ Basic logging test passed")


def test_structured_logging():
    """Test structured logging and session export"""
    print("🧪 Testing structured logging...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = get_logger("test_structured", log_dir=temp_dir)
        
        # Log structured data
        logger.structured_log("test_event", {
            "operation": "screenshot", 
            "url": "https://example.com",
            "success": True
        })
        
        # Log performance data
        logger.performance_log("test_operation", 1.5, file_size=1024, model="test-model")
        
        # Export user session
        session_file = logger.export_user_session()
        
        # Verify session file exists and contains data
        assert Path(session_file).exists()
        session_data = json.loads(Path(session_file).read_text())
        assert session_data["logger_name"] == "test_structured"
        assert "messages" in session_data
        
        print("✅ Structured logging test passed")


def test_report_formatting():
    """Test report formatting functionality"""
    print("🧪 Testing report formatting...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = get_logger("test_report", log_dir=temp_dir)
        
        # Test that report formatting methods work without errors
        logger.report_section("TEST REPORT")
        logger.report_item("Status", "Success")
        logger.report_item("Duration", "1.5s")
        logger.report_subsection("Details")
        
        # Check log file contains report formatting
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) > 0, "Log file should be created"
        
        log_content = log_files[0].read_text()
        assert "TEST REPORT" in log_content
        assert "Status: Success" in log_content
        assert "Duration: 1.5s" in log_content
        
        print("✅ Report formatting test passed")


def test_backward_compatibility():
    """Test backward compatibility with print statements"""
    print("🧪 Testing backward compatibility...")
    
    # Import convenience functions
    from logging_config import user_print, error_print, success_print, warning_print
    
    # Test convenience functions work without errors
    user_print("Test message")
    error_print("Test error") 
    success_print("Test success")
    warning_print("Test warning")
    
    print("✅ Backward compatibility test passed")


def test_performance():
    """Test logging performance doesn't significantly impact operations"""
    print("🧪 Testing logging performance...")
    
    import time
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = get_logger("test_performance", log_dir=temp_dir)
        
        # Test logging many messages quickly
        start_time = time.time()
        for i in range(100):
            logger.user_info(f"Message {i}")
            logger.debug(f"Debug message {i}")
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should complete 100 log messages in under 1 second
        assert duration < 1.0, f"Logging too slow: {duration:.2f}s for 100 messages"
        
        print(f"✅ Performance test passed ({duration:.3f}s for 100 messages)")


def main():
    """Run all logging framework tests"""
    print("🧪 Testing Logging Framework")
    print("=" * 50)
    
    try:
        test_basic_logging()
        test_structured_logging()
        test_report_formatting()
        test_backward_compatibility()
        test_performance()
        
        print("\n" + "=" * 50)
        print("✅ All logging framework tests passed!")
        print("📝 The logging system maintains user experience while adding structured logging")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 