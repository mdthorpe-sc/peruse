#!/usr/bin/env python3
"""
Centralized logging configuration for the screenshot monitoring tool.

This module provides a standardized logging framework that replaces print statements
throughout the codebase while maintaining user-friendly console output.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class UserFriendlyLogger:
    """
    Logger wrapper that provides both structured logging and user-friendly output.
    
    This class maintains the existing user experience while adding proper logging
    infrastructure for debugging and analysis.
    """
    
    def __init__(self, name: str, log_dir: str = "logs", console_level: str = "INFO", file_level: str = "DEBUG"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure logger
        self._setup_logger(console_level, file_level)
        
        # Track user-facing messages separately
        self.user_messages = []
    
    def _setup_logger(self, console_level: str, file_level: str):
        """Set up logging configuration"""
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Console handler (user-friendly output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level.upper()))
        
        # Use colored formatter for console
        console_format = "%(message)s"
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        
        # File handler (detailed logging)
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, file_level.upper()))
        
        # Detailed format for file logging
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def user_info(self, message: str, **kwargs):
        """User-facing informational message (replaces print statements)"""
        self.logger.info(message)
        self.user_messages.append({
            "level": "info",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
    
    def user_success(self, message: str, **kwargs):
        """User-facing success message with ✅ emoji"""
        formatted_message = f"✅ {message}"
        self.logger.info(formatted_message)
        self.user_messages.append({
            "level": "success", 
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
    
    def user_warning(self, message: str, **kwargs):
        """User-facing warning message with ⚠️ emoji"""
        formatted_message = f"⚠️  {message}"
        self.logger.warning(formatted_message)
        self.user_messages.append({
            "level": "warning",
            "message": message, 
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
    
    def user_error(self, message: str, **kwargs):
        """User-facing error message with ❌ emoji"""
        formatted_message = f"❌ {message}"
        self.logger.error(formatted_message)
        self.user_messages.append({
            "level": "error",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
    
    def operation_start(self, operation: str, **details):
        """Log the start of a major operation"""
        self.logger.info(f"🔄 {operation}")
        self.logger.debug(f"Operation started: {operation}", extra=details)
    
    def operation_complete(self, operation: str, **details):
        """Log the completion of a major operation"""
        self.logger.info(f"✅ {operation} completed")
        self.logger.debug(f"Operation completed: {operation}", extra=details)
    
    def debug(self, message: str, **kwargs):
        """Debug logging (only in log files)"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Info logging"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning logging"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Error logging"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical error logging"""
        self.logger.critical(message, extra=kwargs)
    
    def structured_log(self, event_type: str, data: Dict[Any, Any]):
        """Log structured data for analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "logger": self.name,
            **data
        }
        self.logger.debug(f"STRUCTURED_LOG: {json.dumps(log_entry)}")
    
    def performance_log(self, operation: str, duration: float, **metrics):
        """Log performance metrics"""
        self.structured_log("performance", {
            "operation": operation,
            "duration_seconds": duration,
            **metrics
        })
    
    def report_section(self, title: str, separator_char: str = "=", width: int = 60):
        """Print a formatted report section header"""
        separator = separator_char * width
        self.user_info(f"\n{separator}")
        self.user_info(f"📊 {title}")
        self.user_info(separator)
    
    def report_subsection(self, title: str, separator_char: str = "-", width: int = 60):
        """Print a formatted report subsection header"""
        separator = separator_char * width
        self.user_info(separator)
    
    def report_item(self, label: str, value: str, prefix: str = ""):
        """Print a formatted report item"""
        self.user_info(f"{prefix}{label}: {value}")
    
    def export_user_session(self, output_file: str = None) -> str:
        """Export user-facing messages to a file for session analysis"""
        if not output_file:
            output_file = self.log_dir / f"{self.name}_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        session_data = {
            "logger_name": self.name,
            "session_start": datetime.now().isoformat(),
            "messages": self.user_messages
        }
        
        with open(output_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return str(output_file)


# Global logger instances
_loggers: Dict[str, UserFriendlyLogger] = {}


def get_logger(name: str, log_dir: str = "logs", console_level: str = "INFO", file_level: str = "DEBUG") -> UserFriendlyLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (usually module name)
        log_dir: Directory for log files
        console_level: Minimum level for console output (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_level: Minimum level for file output
    
    Returns:
        UserFriendlyLogger instance
    """
    if name not in _loggers:
        _loggers[name] = UserFriendlyLogger(name, log_dir, console_level, file_level)
    
    return _loggers[name]


def configure_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG", 
    log_dir: str = "logs"
):
    """
    Configure global logging settings.
    
    Args:
        console_level: Default console logging level
        file_level: Default file logging level
        log_dir: Default log directory
    """
    # Set defaults for new loggers
    get_logger.__defaults__ = (log_dir, console_level, file_level)


# Convenience functions for backward compatibility with print statements
def user_print(message: str, logger_name: str = "main"):
    """Drop-in replacement for print() that also logs"""
    logger = get_logger(logger_name)
    logger.user_info(message)


def error_print(message: str, logger_name: str = "main"):
    """Drop-in replacement for error print() that also logs"""
    logger = get_logger(logger_name)
    logger.user_error(message)


def success_print(message: str, logger_name: str = "main"):
    """Print success message with logging"""
    logger = get_logger(logger_name)
    logger.user_success(message)


def warning_print(message: str, logger_name: str = "main"):
    """Print warning message with logging"""
    logger = get_logger(logger_name)
    logger.user_warning(message) 