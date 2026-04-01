"""
Windows mail access via Gmail API (READ-ONLY).

Async wrappers around GmailClient that match the interface
expected by server.py (same signatures as mail_access.py).
"""

import asyncio
import logging
from typing import Optional

log = logging.getLogger("jarvis.mail.win32")


def _get_client():
    from ..google_services import get_gmail_client
    return get_gmail_client()


async def get_unread_count() -> dict:
    """Get unread message count."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _get_client().get_unread_count)
    except Exception as e:
        log.warning(f"get_unread_count failed: {e}")
        return {"total": 0, "accounts": {}}


async def get_unread_messages(count: int = 10) -> list[dict]:
    """Get unread messages from inbox."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _get_client().get_unread_messages, count)
    except Exception as e:
        log.warning(f"get_unread_messages failed: {e}")
        return []


async def get_recent_messages(count: int = 10) -> list[dict]:
    """Get most recent messages from inbox."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _get_client().get_recent_messages, count)
    except Exception as e:
        log.warning(f"get_recent_messages failed: {e}")
        return []


async def get_messages_from_account(account_name: str, count: int = 10) -> list[dict]:
    """Get messages from a specific account/sender."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None, _get_client().get_messages_from_account, account_name, count
        )
    except Exception as e:
        log.warning(f"get_messages_from_account failed: {e}")
        return []


async def search_mail(query: str, count: int = 10) -> list[dict]:
    """Search mail by query."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _get_client().search_mail, query, count)
    except Exception as e:
        log.warning(f"search_mail failed: {e}")
        return []


async def read_message(subject_match: str) -> Optional[dict]:
    """Read full content of a message matching subject."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _get_client().read_message, subject_match)
    except Exception as e:
        log.warning(f"read_message failed: {e}")
        return None


async def get_mail_accounts() -> list[str]:
    """Get list of configured mail account names."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _get_client().get_accounts)
    except Exception as e:
        log.warning(f"get_mail_accounts failed: {e}")
        return []
