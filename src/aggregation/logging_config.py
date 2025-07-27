"""
Logging configuration for TrendCreate aggregation system
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_to_file: bool = True, log_to_console: bool = True) -> logging.Logger:
    """
    Setup comprehensive logging for the aggregation system
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
    
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("aggregation")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Console shows INFO and above
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handlers
    if log_to_file:
        # Daily log file (rotates daily, keeps 30 days)
        daily_log_file = logs_dir / f"aggregation_{datetime.now().strftime('%Y-%m-%d')}.log"
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            filename=daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.DEBUG)  # File logs everything
        daily_handler.setFormatter(formatter)
        logger.addHandler(daily_handler)
        
        # Error log file (only errors and critical)
        error_log_file = logs_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # Performance log file (for timing and metrics)
        perf_log_file = logs_dir / "performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=perf_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        
        # Custom formatter for performance logs
        perf_formatter = logging.Formatter(
            fmt='%(asctime)s | PERF | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        perf_handler.setFormatter(perf_formatter)
        
        # Create performance logger
        perf_logger = logging.getLogger("aggregation.performance")
        perf_logger.setLevel(logging.INFO)
        perf_logger.addHandler(perf_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance for a specific module"""
    if name:
        return logging.getLogger(f"aggregation.{name}")
    return logging.getLogger("aggregation")


def get_performance_logger() -> logging.Logger:
    """Get the performance logger for timing and metrics"""
    return logging.getLogger("aggregation.performance")


def log_performance_metric(operation: str, duration: float, **kwargs):
    """
    Log a performance metric
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        **kwargs: Additional metadata
    """
    perf_logger = get_performance_logger()
    
    metadata = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    perf_logger.info(f"{operation} | {duration:.3f}s | {metadata}")


# Performance tracking decorator
def track_performance(operation_name: str = None):
    """Decorator to automatically track function performance"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance_metric(operation, duration, status="success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance_metric(operation, duration, status="error", error=str(e))
                raise
        
        return wrapper
    return decorator


# Context manager for operation logging
class LoggedOperation:
    """Context manager for logging operations with timing"""
    
    def __init__(self, operation_name: str, logger: logging.Logger = None, **metadata):
        self.operation_name = operation_name
        self.logger = logger or get_logger()
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation_name} in {duration:.3f}s")
            log_performance_metric(self.operation_name, duration, status="success", **self.metadata)
        else:
            self.logger.error(f"Failed {self.operation_name} after {duration:.3f}s: {exc_val}")
            log_performance_metric(self.operation_name, duration, status="error", error=str(exc_val), **self.metadata)


# Initialize logging when module is imported
import time
_default_logger = None

def init_logging():
    """Initialize default logging configuration"""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging()
    return _default_logger
