"""
Google API clients for JARVIS — Calendar and Gmail.

All access is READ-ONLY by design.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

log = logging.getLogger("jarvis.google_services")


def _build_service(api_name: str, api_version: str):
    """Build a Google API service client."""
    from googleapiclient.discovery import build
    from .google_auth import get_credentials

    creds = get_credentials()
    if not creds:
        return None
    return build(api_name, api_version, credentials=creds)


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

class GoogleCalendarClient:
    """Read-only Google Calendar client."""

    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = _build_service("calendar", "v3")
        return self._service

    def get_todays_events(self) -> list[dict]:
        """Get all events for today."""
        service = self._get_service()
        if not service:
            return []

        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        try:
            result = service.events().list(
                calendarId="primary",
                timeMin=start_of_day.isoformat() + "Z",
                timeMax=end_of_day.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = []
            for item in result.get("items", []):
                start = item["start"]
                all_day = "date" in start and "dateTime" not in start

                if all_day:
                    time_str = "ALL_DAY"
                    start_dt = datetime.strptime(start["date"], "%Y-%m-%d")
                else:
                    start_dt = datetime.fromisoformat(start["dateTime"])
                    time_str = start_dt.strftime("%I:%M %p").lstrip("0")

                events.append({
                    "calendar": item.get("organizer", {}).get("displayName", "Primary"),
                    "title": item.get("summary", "(No title)"),
                    "start": time_str,
                    "start_dt": start_dt,
                    "all_day": all_day,
                })
            return events

        except Exception as e:
            log.warning(f"Failed to fetch calendar events: {e}")
            return []

    def get_upcoming_events(self, hours: int = 4) -> list[dict]:
        """Get events in the next N hours."""
        events = self.get_todays_events()
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        return [
            e for e in events
            if not e["all_day"] and e.get("start_dt") and now <= e["start_dt"] <= cutoff
        ]

    def get_next_event(self) -> Optional[dict]:
        """Get the next upcoming event."""
        upcoming = self.get_upcoming_events(hours=24)
        return upcoming[0] if upcoming else None

    def get_calendar_names(self) -> list[str]:
        """Get list of all calendar names."""
        service = self._get_service()
        if not service:
            return []
        try:
            result = service.calendarList().list().execute()
            return [cal.get("summary", "") for cal in result.get("items", [])]
        except Exception as e:
            log.warning(f"Failed to list calendars: {e}")
            return []

    def get_events_for_range(self, start: datetime, end: datetime) -> list[dict]:
        """Get events in a specific time range (for multi-calendar support)."""
        service = self._get_service()
        if not service:
            return []

        all_events = []
        try:
            # Fetch from all calendars
            calendars = service.calendarList().list().execute()
            for cal in calendars.get("items", []):
                cal_id = cal["id"]
                cal_name = cal.get("summary", cal_id)
                try:
                    result = service.events().list(
                        calendarId=cal_id,
                        timeMin=start.isoformat() + "Z",
                        timeMax=end.isoformat() + "Z",
                        singleEvents=True,
                        orderBy="startTime",
                    ).execute()

                    for item in result.get("items", []):
                        ev_start = item["start"]
                        all_day = "date" in ev_start and "dateTime" not in ev_start

                        if all_day:
                            time_str = "ALL_DAY"
                            start_dt = datetime.strptime(ev_start["date"], "%Y-%m-%d")
                        else:
                            start_dt = datetime.fromisoformat(ev_start["dateTime"])
                            time_str = start_dt.strftime("%I:%M %p").lstrip("0")

                        all_events.append({
                            "calendar": cal_name,
                            "title": item.get("summary", "(No title)"),
                            "start": time_str,
                            "start_dt": start_dt,
                            "all_day": all_day,
                        })
                except Exception:
                    continue

        except Exception as e:
            log.warning(f"Failed to fetch events: {e}")

        all_events.sort(key=lambda e: (not e["all_day"], e.get("start_dt") or datetime.max))
        return all_events


# ---------------------------------------------------------------------------
# Gmail (READ-ONLY)
# ---------------------------------------------------------------------------

class GmailClient:
    """Read-only Gmail client."""

    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = _build_service("gmail", "v1")
        return self._service

    def _get_message_detail(self, msg_id: str) -> Optional[dict]:
        """Fetch a single message's details."""
        service = self._get_service()
        if not service:
            return None
        try:
            msg = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()

            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

            # Extract preview from snippet
            preview = msg.get("snippet", "")[:150]

            return {
                "sender": headers.get("from", "Unknown"),
                "subject": headers.get("subject", "(No subject)"),
                "date": headers.get("date", ""),
                "read": "UNREAD" not in msg.get("labelIds", []),
                "preview": preview,
                "id": msg_id,
            }
        except Exception as e:
            log.warning(f"Failed to get message {msg_id}: {e}")
            return None

    def get_unread_count(self) -> dict:
        """Get unread message count."""
        service = self._get_service()
        if not service:
            return {"total": 0, "accounts": {}}

        try:
            # Get total unread count
            result = service.users().messages().list(
                userId="me", q="is:unread in:inbox", maxResults=1
            ).execute()
            total = result.get("resultSizeEstimate", 0)

            # Gmail doesn't have "accounts" like Apple Mail, use labels
            profile = service.users().getProfile(userId="me").execute()
            email = profile.get("emailAddress", "Gmail")

            return {
                "total": total,
                "accounts": {email: total},
            }
        except Exception as e:
            log.warning(f"Failed to get unread count: {e}")
            return {"total": 0, "accounts": {}}

    def get_unread_messages(self, count: int = 10) -> list[dict]:
        """Get unread messages from inbox."""
        return self._list_messages(query="is:unread in:inbox", count=count)

    def get_recent_messages(self, count: int = 10) -> list[dict]:
        """Get most recent messages from inbox."""
        return self._list_messages(query="in:inbox", count=count)

    def get_messages_from_account(self, account_name: str, count: int = 10) -> list[dict]:
        """Get messages from a specific sender/account."""
        return self._list_messages(query=f"from:{account_name}", count=count)

    def search_mail(self, query: str, count: int = 10) -> list[dict]:
        """Search mail by query string."""
        return self._list_messages(query=query, count=count)

    def read_message(self, subject_match: str) -> Optional[dict]:
        """Read full content of a message matching subject."""
        service = self._get_service()
        if not service:
            return None

        try:
            result = service.users().messages().list(
                userId="me", q=f"subject:{subject_match}", maxResults=1
            ).execute()

            messages = result.get("messages", [])
            if not messages:
                return None

            msg = service.users().messages().get(
                userId="me", id=messages[0]["id"], format="full"
            ).execute()

            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

            # Extract body text
            body = self._extract_body(msg.get("payload", {}))

            return {
                "sender": headers.get("from", "Unknown"),
                "subject": headers.get("subject", "(No subject)"),
                "date": headers.get("date", ""),
                "content": body[:3000],  # Truncate like Apple Mail version
            }
        except Exception as e:
            log.warning(f"Failed to read message: {e}")
            return None

    def get_accounts(self) -> list[str]:
        """Get the Gmail address (single account)."""
        service = self._get_service()
        if not service:
            return []
        try:
            profile = service.users().getProfile(userId="me").execute()
            return [profile.get("emailAddress", "")]
        except Exception:
            return []

    def _list_messages(self, query: str, count: int = 10) -> list[dict]:
        """List messages matching a query."""
        service = self._get_service()
        if not service:
            return []

        try:
            result = service.users().messages().list(
                userId="me", q=query, maxResults=count
            ).execute()

            messages = []
            for msg_ref in result.get("messages", []):
                detail = self._get_message_detail(msg_ref["id"])
                if detail:
                    messages.append(detail)

            return messages
        except Exception as e:
            log.warning(f"Failed to list messages: {e}")
            return []

    def _extract_body(self, payload: dict) -> str:
        """Extract plain text body from a Gmail message payload."""
        import base64

        # Direct body
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        # Multipart — find text/plain
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            # Recurse into nested parts
            if part.get("parts"):
                result = self._extract_body(part)
                if result:
                    return result

        return "(Could not extract message body)"


# Module-level singletons
_calendar_client = None
_gmail_client = None


def get_calendar_client() -> GoogleCalendarClient:
    global _calendar_client
    if _calendar_client is None:
        _calendar_client = GoogleCalendarClient()
    return _calendar_client


def get_gmail_client() -> GmailClient:
    global _gmail_client
    if _gmail_client is None:
        _gmail_client = GmailClient()
    return _gmail_client
