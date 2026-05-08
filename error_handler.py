"""Centralized error handler with auto-recovery suggestions."""
import traceback
from typing import Any, Dict


class AppError(Exception):
    """Custom error with user-friendly message and recovery suggestion."""
    def __init__(self, message: str, suggestion: str = ""):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


def handle_error(error: Exception, context: str = "") -> Dict[str, str]:
    """Convert any error into user-friendly dict with recovery suggestions."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    suggestions = {
        "ImportError": "A required package is missing. Check requirements.txt",
        "ModuleNotFoundError": "Install missing package: pip install <package>",
        "ConnectionError": "Check your internet connection",
        "Timeout": "API took too long. Try again or use a different provider",
        "AuthenticationError": "Invalid API key. Get a new one",
        "PermissionError": "Check file permissions",
        "FileNotFoundError": "File missing - check the path",
        "ValueError": "Invalid input - check the format",
        "KeyError": "Required field missing in response",
        "json.JSONDecodeError": "AI returned invalid JSON - try again",
    }
    
    suggestion = suggestions.get(error_type, "Try refreshing the page or contact support")
    
    # Specific Gemini errors
    if "404" in error_msg and "gemini" in error_msg.lower():
        suggestion = "Gemini model not available. The app will try other models automatically."
    elif "quota" in error_msg.lower():
        suggestion = "API quota exceeded. Wait or use a different key."
    elif "invalid api key" in error_msg.lower() or "401" in error_msg:
        suggestion = "API key is invalid. Get a fresh one from the provider."
    elif "rate limit" in error_msg.lower():
        suggestion = "Too many requests. Wait 60 seconds and try again."
    
    return {
        "error": f"{error_type}: {error_msg}",
        "suggestion": suggestion,
        "context": context,
    }


def safe_call(func, *args, default=None, context: str = "", **kwargs):
    """Call function safely, return default on error."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return handle_error(e, context)
