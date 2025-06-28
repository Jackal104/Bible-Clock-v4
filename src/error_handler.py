"""
Centralized error handling and recovery for Bible Clock.
"""

import logging
import traceback
from datetime import datetime
from typing import Optional, Callable, Any
import functools

class BibleClockError(Exception):
    """Base exception for Bible Clock errors."""
    pass

class DisplayError(BibleClockError):
    """Display-related errors."""
    pass

class VerseError(BibleClockError):
    """Verse retrieval errors."""
    pass

class VoiceError(BibleClockError):
    """Voice control errors."""
    pass

class ErrorHandler:
    """Centralized error handling and recovery."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.recovery_strategies = {}
    
    def with_retry(self, max_retries: int = 3, delay: float = 1.0):
        """Decorator for automatic retry with exponential backoff."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            wait_time = delay * (2 ** attempt)
                            self.logger.warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {wait_time}s..."
                            )
                            import time
                            time.sleep(wait_time)
                        else:
                            self.logger.error(
                                f"All {max_retries + 1} attempts failed for {func.__name__}"
                            )
                
                raise last_exception
            return wrapper
        return decorator
    
    def handle_gracefully(self, fallback_value: Any = None):
        """Decorator for graceful error handling with fallback."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error in {func.__name__}: {e}")
                    self._log_error_details(func.__name__, e)
                    return fallback_value
            return wrapper
        return decorator
    
    def _log_error_details(self, function_name: str, error: Exception):
        """Log detailed error information."""
        error_info = {
            'function': function_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(f"Detailed error info: {error_info}")
        
        # Track error frequency
        error_key = f"{function_name}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Alert if error frequency is high
        if self.error_counts[error_key] > 5:
            self.logger.critical(
                f"High error frequency detected: {error_key} "
                f"occurred {self.error_counts[error_key]} times"
            )

# Global error handler instance
error_handler = ErrorHandler()