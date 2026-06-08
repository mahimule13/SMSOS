"""services.py for accounts app.

This module is intended to hold business logic that can be reused by views,
admin actions, management commands, etc.

Currently includes helper functions to support bulk SMS sending to parents
based on phone numbers stored in the system.

NOTE: The actual SMS provider integration is intentionally left as a stub.
Wire it up to your chosen provider (e.g., Twilio, MSG91, PotlaSMS API, etc.).
"""

from __future__ import annotations
from email.mime import message
from unittest.mock import call
from operator import call
from xmlrpc import client
import requests
from django.conf import settings
from dataclasses import dataclass
from typing import Iterable, List, Sequence
from twilio.rest import Client



@dataclass(frozen=True)
class SmsRecipient:
    phone: str
    name: str | None = None


def normalize_phone(phone: str) -> str:
    """Normalize phone number.

    - Strips spaces and hyphens
    - Keeps only digits (very basic normalization)

    You can enhance this based on your expected country/format.
    """
    if phone is None:
        return ""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    return digits


def filter_valid_phones(phones: Iterable[str], *, min_len: int = 10, max_len: int = 15) -> List[str]:
    """Return a de-duplicated list of normalized valid phone numbers."""
    cleaned = []
    seen = set()

    for p in phones:
        np = normalize_phone(p)
        if not np:
            continue
        if not (min_len <= len(np) <= max_len):
            continue
        if np in seen:
            continue
        seen.add(np)
        cleaned.append(np)

    return cleaned


def build_personalized_message(*, template: str, recipient_name: str | None = None, **kwargs) -> str:
    """Build message from a template.

    Supported placeholders:
    - {name}
    - any keys from kwargs

    Example: "Hello {name}, your fee is due".
    """
    ctx = dict(kwargs)
    ctx.setdefault("name", recipient_name or "")
    return template.format(**ctx)

import requests
from django.conf import settings

def send_bulk_sms(*, phones, message):

    phones = filter_valid_phones(phones)

    print("SMS SENT TO:", phones)
    print("MESSAGE:",)
    print(message)
    return {
        "sent": len(phones),
        "failed": 0,
    }
# def send_bulk_sms(*, phones, message):

#     phones = filter_valid_phones(phones)

#     if not phones:
#         return {
#             "sent": 0,
#             "failed": 0,
#         }

#     url = "https://www.fast2sms.com/dev/bulkV2"

#     payload = {
#         "route": "q",
#         "message": message,
#         "language": "english",
#         "flash": 0,
#         "numbers": ",".join(phones),
#     }

#     headers = {
#         "authorization": settings.FAST2SMS_API_KEY.strip(),
#         "Content-Type": "application/json"
#     }

#     try:

#         response = requests.post(
#             url,
#             json=payload,
#             headers=headers
#         )

#         data = response.json()

#         print("FAST2SMS RESPONSE =", data)

#         return {
#             "sent": len(phones),
#             "failed": 0,
#             "response": data,
#         }

#     except Exception as e:

#         print("SMS ERROR =", str(e))

#         return {
#             "sent": 0,
#             "failed": len(phones),
#             "error": str(e),
#         }
def send_parent_bulk_sms(*, recipients: Iterable[SmsRecipient], template: str, extra_context: dict | None = None) -> dict:
    """High-level helper to send parent messages.

    recipients: iterable of SmsRecipient (phone + optional name)
    template: message template string
    extra_context: extra placeholder values for template
    """
    extra_context = extra_context or {}

    normalized_phones = []
    personalized_messages: List[tuple[str, str]] = []

    for r in recipients:
        phone = normalize_phone(r.phone)
        if not phone:
            continue
        normalized_phones.append(phone)
        msg = build_personalized_message(
            template=template,
            recipient_name=r.name,
            **extra_context,
        )
        personalized_messages.append((phone, msg))

    # If you want single-message bulk send, ensure all messages are identical.
    # Many SMS providers support sending one payload to many recipients.
    # For simplicity: if messages differ, we'll still call send_bulk_sms once per unique message.
    unique_messages = {}
    for phone, msg in personalized_messages:
        unique_messages.setdefault(msg, []).append(phone)

    results = []
    for msg, phones in unique_messages.items():
        results.append(send_bulk_sms(phones=filter_valid_phones(phones), message=msg))

    sent_total = sum(r.get("sent", 0) for r in results)
    return {
        "sent": sent_total,
        "batches": results,
    }



 



