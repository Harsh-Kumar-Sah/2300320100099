"""
Logging Middleware Package
==========================
A reusable logging middleware that sends structured logs to the 
Affordmed evaluation server.

Usage:
    from logging_middleware import Log
    
    Log("backend", "info", "handler", "Request received successfully")
"""

from .logger import Log
from .config import initialize, get_token

__all__ = ["Log", "initialize", "get_token"]
