"""
Logger Module
=============
Core logging function that sends structured log entries to the 
Affordmed evaluation server.

Validates all inputs against the allowed values before making the API call.
"""

import requests
from .config import get_token, LOG_URL

# =============================================================================
# Allowed Values (enforced by the test server)
# =============================================================================
VALID_STACKS = {"backend", "frontend"}

VALID_LEVELS = {"debug", "info", "warn", "error", "fatal"}

BACKEND_ONLY_PACKAGES = {
    "cache", "controller", "cron_job", "db", "domain",
    "handler", "repository", "route", "service",
}

FRONTEND_ONLY_PACKAGES = {
    "api", "component", "hook", "page", "state", "style",
}

SHARED_PACKAGES = {"auth", "config", "middleware", "utils"}

VALID_PACKAGES = {
    "backend": BACKEND_ONLY_PACKAGES | SHARED_PACKAGES,
    "frontend": FRONTEND_ONLY_PACKAGES | SHARED_PACKAGES,
}


def _validate_inputs(stack: str, level: str, package: str, message: str) -> None:
    """
    Validate log inputs against allowed values.
    
    Raises:
        ValueError: If any input is invalid.
    """
    if stack not in VALID_STACKS:
        raise ValueError(
            f"Invalid stack '{stack}'. Must be one of: {VALID_STACKS}"
        )

    if level not in VALID_LEVELS:
        raise ValueError(
            f"Invalid level '{level}'. Must be one of: {VALID_LEVELS}"
        )

    if package not in VALID_PACKAGES.get(stack, set()):
        raise ValueError(
            f"Invalid package '{package}' for stack '{stack}'. "
            f"Must be one of: {VALID_PACKAGES[stack]}"
        )

    if not message or not isinstance(message, str):
        raise ValueError("Message must be a non-empty string.")

    # Server requires message to be at least 5 characters
    if len(message) < 5:
        raise ValueError(
            f"Message must be at least 5 characters (got {len(message)}). "
            f"Provide a more descriptive log message."
        )


# Maximum message length accepted by the evaluation server
MAX_MESSAGE_LENGTH = 48


def Log(stack: str, level: str, package: str, message: str) -> dict:
    """
    Send a structured log entry to the evaluation server.
    
    Args:
        stack: Application stack — "backend" or "frontend"
        level: Log severity — "debug", "info", "warn", "error", "fatal"
        package: Source package — varies by stack (see VALID_PACKAGES)
        message: Descriptive log message
    
    Returns:
        dict: Server response containing logID and confirmation message.
            Example: {"logID": "uuid-here", "message": "log created successfully"}
    
    Raises:
        ValueError: If inputs don't match allowed values.
        RuntimeError: If the API call fails.
    
    Example:
        >>> Log("backend", "info", "handler", "Request processed successfully")
        {"logID": "a4aad02e-...", "message": "log created successfully"}
    """
    # Validate inputs before making the API call
    _validate_inputs(stack, level, package, message)

    # Truncate message to server's max length (48 chars)
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH]

    # Get a valid auth token
    token = get_token()

    # Build request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message,
    }

    # Send log to evaluation server
    try:
        response = requests.post(LOG_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        # We intentionally don't raise here to avoid breaking the app
        # due to a logging failure. Instead, we print to stderr as fallback.
        import sys
        print(
            f"[LOGGING MIDDLEWARE ERROR] Failed to send log: {e}. "
            f"Payload: {payload}",
            file=sys.stderr,
        )
        return {"logID": None, "message": f"Log send failed: {e}"}
