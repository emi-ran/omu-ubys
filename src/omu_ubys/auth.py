"""
OMU-UBYS Authentication Module

Handles CSRF token extraction, login flow, and session management.
"""

import re
import httpx
from typing import Optional

from .exceptions import LoginError, CSRFTokenError, NetworkError


# Default headers to mimic a real browser
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

BASE_URL = "https://ubys.omu.edu.tr"


def create_session() -> httpx.Client:
    """
    Create a new HTTP session with default headers.
    
    Returns:
        httpx.Client: Configured HTTP client with cookies enabled
    """
    return httpx.Client(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=30.0,
    )


def get_csrf_token(session: httpx.Client) -> str:
    """
    Fetch the CSRF token from the UBYS homepage.
    
    Args:
        session: Active HTTP session
        
    Returns:
        str: The CSRF token value
        
    Raises:
        CSRFTokenError: If token cannot be extracted
        NetworkError: If connection fails
    """
    try:
        response = session.get(BASE_URL)
        response.raise_for_status()
    except httpx.RequestError as e:
        raise NetworkError(f"Failed to connect to UBYS: {e}") from e
    
    # Extract token from hidden input
    match = re.search(
        r'name="__RequestVerificationToken".*?value="([^"]+)"',
        response.text
    )
    
    if not match:
        raise CSRFTokenError("Could not find CSRF token in page. UBYS might be unavailable.")
    
    return match.group(1)


def login(session: httpx.Client, username: str, password: str) -> dict:
    """
    Perform login to UBYS.
    
    Args:
        session: Active HTTP session
        username: Student number
        password: Password
        
    Returns:
        dict: Login response containing user info
        
    Raises:
        LoginError: If login fails
        CSRFTokenError: If CSRF token cannot be obtained
        NetworkError: If connection fails
    """
    # Get CSRF token first
    csrf_token = get_csrf_token(session)
    
    # Prepare login payload
    payload = {
        "__RequestVerificationToken": csrf_token,
        "username": username,
        "password": password,
        "X-Requested-With": "XMLHttpRequest",
    }
    
    # Add AJAX header
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": f"{BASE_URL}/",
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/Account/Login",
            data=payload,
            headers=headers,
        )
    except httpx.RequestError as e:
        raise NetworkError(f"Login request failed: {e}") from e
    
    # Parse response
    try:
        data = response.json()
    except Exception:
        # Sometimes UBYS returns HTML on error
        if "errorMessage" in response.text:
            raise LoginError("Login failed. Please check your credentials.")
        raise LoginError(f"Unexpected response from server: {response.text[:200]}")
    
    # Check for error in response
    if data.get("errorType") == "error" or data.get("errorMessage"):
        error_msg = data.get("errorMessage", "Unknown error")
        raise LoginError(f"Login failed: {error_msg}")
    
    return data


def is_session_valid(session: httpx.Client) -> bool:
    """
    Check if the current session is still valid.
    
    Args:
        session: Active HTTP session
        
    Returns:
        bool: True if session is valid, False if expired
    """
    try:
        response = session.get(
            f"{BASE_URL}/AIS/Student/Home/Index",
            follow_redirects=False,
        )
        # If redirected to login page, session is expired
        if response.status_code == 302:
            location = response.headers.get("location", "")
            if "Account/Login" in location:
                return False
        return response.status_code == 200
    except Exception:
        return False
