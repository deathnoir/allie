"""
Google OAuth 2.0 authentication for JARVIS on Windows.

Handles the Desktop app OAuth flow:
1. User downloads credentials.json from Google Cloud Console
2. User runs: python -m jarvis_platform.google_auth
3. Browser opens to Google consent screen
4. Token saved to data/google_token.json (auto-refreshes)

Required Google Cloud APIs:
- Google Calendar API
- Gmail API

OAuth scopes (read-only):
- https://www.googleapis.com/auth/calendar.readonly
- https://www.googleapis.com/auth/gmail.readonly
"""

import json
import logging
from pathlib import Path

log = logging.getLogger("jarvis.google_auth")

DATA_DIR = Path(__file__).parent.parent / "data"
CREDENTIALS_PATH = DATA_DIR / "google_credentials.json"
TOKEN_PATH = DATA_DIR / "google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_credentials():
    """Get valid Google API credentials, refreshing if needed.

    Returns google.oauth2.credentials.Credentials or None.
    Raises RuntimeError if not authenticated.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        log.warning("google-auth not installed. Run: pip install google-auth-oauthlib google-api-python-client")
        return None

    creds = None

    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as e:
            log.warning(f"Failed to load token: {e}")

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception as e:
            log.warning(f"Token refresh failed: {e}")

    return None


def _save_token(creds) -> None:
    """Save credentials to token file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())


def is_authenticated() -> bool:
    """Check if Google APIs are authenticated."""
    return get_credentials() is not None


def run_auth_flow() -> bool:
    """Run the interactive OAuth flow. Opens browser for consent.

    Returns True on success.
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: google-auth-oauthlib not installed.")
        print("Run: pip install google-auth-oauthlib google-api-python-client")
        return False

    if not CREDENTIALS_PATH.exists():
        print(f"ERROR: Credentials file not found at {CREDENTIALS_PATH}")
        print()
        print("To set up Google API access:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project (or select existing)")
        print("3. Enable 'Google Calendar API' and 'Gmail API'")
        print("4. Go to Credentials → Create Credentials → OAuth client ID")
        print("5. Select 'Desktop app' as application type")
        print("6. Download the JSON file")
        print(f"7. Save it as: {CREDENTIALS_PATH}")
        print()
        print("Then run this command again.")
        return False

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH), SCOPES
        )
        creds = flow.run_local_server(port=0)
        _save_token(creds)
        print("Authentication successful! Token saved.")
        print("JARVIS can now access your Google Calendar and Gmail.")
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False


# Allow running as: python -m jarvis_platform.google_auth
if __name__ == "__main__":
    print("JARVIS — Google API Authentication")
    print("=" * 40)
    run_auth_flow()
