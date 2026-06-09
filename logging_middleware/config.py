"""
Configuration & Authentication Module
======================================
Manages credentials and auth token lifecycle for the evaluation server.
Caches the JWT token and refreshes it automatically when expired.
"""

import time
import requests
import os
from dotenv import load_dotenv

# Automatically finds and reads the .env file
load_dotenv()

# Pull individual settings into variables
email = os.getenv("EMAIL")
name = os.getenv("NAME")
rollNo = os.getenv("ROLLNO")
accessCode = os.getenv("ACCESSCODE")
clientID = os.getenv("CLIENTID")
clientSecret = os.getenv("CLIENTSECRET")


# =============================================================================
# CREDENTIALS — FILL IN YOUR DETAILS BELOW
# =============================================================================
CREDENTIALS = {
    "email": email,
    "name": name,
    "rollNo": rollNo,
    "accessCode": accessCode,
    "clientID": clientID,
    "clientSecret": clientSecret,
}

# =============================================================================
# API Configuration
# =============================================================================
BASE_URL = "http://4.224.186.213/evaluation-service"
AUTH_URL = f"{BASE_URL}/auth"
LOG_URL = f"{BASE_URL}/logs"

# =============================================================================
# Token Cache
# =============================================================================
_token_cache = {
    "access_token": None,
    "expires_at": 0,  # Unix timestamp
}


def initialize(email: str, name: str, roll_no: str, access_code: str,
               client_id: str, client_secret: str) -> None:
    """
    Initialize credentials programmatically instead of editing the file.
    
    Args:
        email: Registered email address
        name: Registered name
        roll_no: University roll number
        access_code: Access code from email
        client_id: Client ID from registration response
        client_secret: Client secret from registration response
    """
    CREDENTIALS["email"] = email
    CREDENTIALS["name"] = name
    CREDENTIALS["rollNo"] = roll_no
    CREDENTIALS["accessCode"] = access_code
    CREDENTIALS["clientID"] = client_id
    CREDENTIALS["clientSecret"] = client_secret


def _is_token_valid() -> bool:
    """Check if the cached token is still valid (with 60s buffer)."""
    return (
        _token_cache["access_token"] is not None
        and time.time() < _token_cache["expires_at"] - 60
    )


def get_token() -> str:
    """
    Get a valid Bearer token. Fetches a new one if the cached token
    is expired or missing.
    
    Returns:
        str: A valid JWT access token.
    
    Raises:
        RuntimeError: If authentication fails.
    """
    if _is_token_valid():
        return _token_cache["access_token"]

    # Request a new token
    try:
        response = requests.post(AUTH_URL, json=CREDENTIALS, timeout=10)
        response.raise_for_status()
        data = response.json()

        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = data["expires_in"]

        return _token_cache["access_token"]

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Authentication failed: {e}. "
            f"Status: {getattr(e.response, 'status_code', 'N/A')}. "
            f"Ensure credentials in config.py are correct."
        ) from e
