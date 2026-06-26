from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional
from xml.sax.saxutils import escape

from django.conf import settings  # type: ignore
from twilio.rest import Client  # type: ignore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParentContact:
    phone: str
    name: Optional[str] = None


def _normalize_phone(phone: str) -> str:
    """Return only digits from an input phone string."""
    if not phone:
        return ""
    return "".join(ch for ch in str(phone).strip() if ch.isdigit())


def _to_e164_or_none(raw_phone: str) -> Optional[str]:
    """Best-effort conversion to E.164 for this project.

    - If input already includes '+', keep it and validate digits length.
    - If digits are 10 -> assume India (+91)
    - Otherwise invalid.
    """
    if raw_phone is None:
        return None

    s = str(raw_phone).strip()
    if not s:
        return None

    if s.startswith('+'):
        digits = ''.join(ch for ch in s if ch.isdigit())
        if 10 <= len(digits) <= 15:
            return '+' + digits
        return None

    digits = _normalize_phone(s)
    if not digits:
        return None

    if len(digits) == 10:
        return '+91' + digits

    return None


def _classify_twilio_failure(exc: Exception) -> dict:
    """Map Twilio errors to human-readable categories."""
    message = str(exc) or ""
    code = getattr(exc, 'code', None)
    code_str = str(code) if code is not None else None

    m_lower = message.lower()

    if 'unverified' in m_lower:
        return {
            'failure_reason': 'unverified number',
            'twilio_error_code': code_str,
            'twilio_error_message': message,
        }

    if ('authentication' in m_lower) or ('auth' in m_lower and 'token' in m_lower):
        return {
            'failure_reason': 'authentication failed',
            'twilio_error_code': code_str,
            'twilio_error_message': message,
        }

    if (
        'permission' in m_lower
        or 'not authorized' in m_lower
        or 'account not authorized' in m_lower
    ):
        return {
            'failure_reason': 'twilio permission issue',
            'twilio_error_code': code_str,
            'twilio_error_message': message,
        }

    if 'trial' in m_lower and (
        'number' in m_lower or 'verified' in m_lower or 'restriction' in m_lower
    ):
        return {
            'failure_reason': 'trial account restriction',
            'twilio_error_code': code_str,
            'twilio_error_message': message,
        }

    if 'invalid' in m_lower or 'number' in m_lower:
        return {
            'failure_reason': 'invalid number',
            'twilio_error_code': code_str,
            'twilio_error_message': message,
        }

    return {
        'failure_reason': 'twilio error',
        'twilio_error_code': code_str,
        'twilio_error_message': message,
        'twilio_error_more_info': getattr(exc, 'more_info', None),
    }



def _iter_valid_phones(
    phones: Iterable[str],
    *,
    min_len: int = 10,
    max_len: int = 15,
) -> List[str]:
    """Normalize, validate, and remove duplicate phone numbers."""
    seen = set()
    valid_numbers: List[str] = []

    for phone in phones:
        e164 = _to_e164_or_none(phone)
        if not e164:
            continue

        digits = ''.join(ch for ch in e164 if ch.isdigit())
        if not (min_len <= len(digits) <= max_len):
            continue

        if e164 in seen:
            continue

        seen.add(e164)
        valid_numbers.append(e164)

    return valid_numbers


def trigger_twilio_ivr_calls(
    *,
    contacts: Iterable[ParentContact],
    message: str,
) -> dict:
    logger.info("[IVR] trigger_twilio_ivr_calls called")

    # Materialize iterable for logging and stable iteration
    try:
        contacts_list = list(contacts)
    except Exception:
        logger.exception("[IVR] Failed to materialize contacts iterable")
        contacts_list = []

    logger.info("[IVR] contacts_count=%s", len(contacts_list))

    # Read Twilio credentials
    account_sid = str(getattr(settings, "TWILIO_ACCOUNT_SID", "")).strip()
    auth_token = str(getattr(settings, "TWILIO_AUTH_TOKEN", "")).strip()
    from_number = str(getattr(settings, "TWILIO_PHONE_NUMBER", "")).strip()

    # Validate configuration
    missing = []
    if not account_sid:
        missing.append("TWILIO_ACCOUNT_SID")
    if not auth_token:
        missing.append("TWILIO_AUTH_TOKEN")
    if not from_number:
        missing.append("TWILIO_PHONE_NUMBER")

    if missing:
        raise RuntimeError("Twilio IVR misconfigured. Missing: " + ", ".join(missing))

    if not from_number:
        raise RuntimeError("Twilio IVR misconfigured. Missing TWILIO_PHONE_NUMBER")

    client = Client(account_sid, auth_token)

    phones = [c.phone for c in contacts_list if c.phone]
    valid_phones = _iter_valid_phones(phones)

    if not valid_phones:
        logger.warning(
            "[IVR] no valid destination phone numbers after normalization; skipping call request"
        )
        return {
            "attempted": 0,
            "successful_calls": 0,
            "results": [],
        }

    safe_message = escape(message)

    twiml = f"""
<Response>
    <Say voice=\"alice\" language=\"en-IN\">
        {safe_message}
    </Say>
</Response>
"""

    call_results: List[dict] = []

    for idx, phone in enumerate(valid_phones, start=1):
        try:
            logger.info("[IVR] (%s/%s) creating call to=%s", idx, len(valid_phones), phone)

            call = client.calls.create(
                to=phone,
                from_=from_number,
                twiml=twiml,
            )

            call_results.append({
                "phone": phone,
                "status": "SUCCESS",
                "call_sid": call.sid,
            })

        except Exception as e:
            failure = _classify_twilio_failure(e)
            logger.exception(
                "[IVR] call FAILED to=%s from=%s reason=%s twilio_code=%s", 
                phone,
                from_number,
                failure.get('failure_reason'),
                failure.get('twilio_error_code'),
            )


            call_results.append({
                "phone": phone,
                "status": "FAILED",
                "error": str(e),  # backward compatible
                **failure,
            })

    successful_calls = sum(1 for r in call_results if r.get("status") == "SUCCESS")
    logger.info("[IVR] successful_calls=%s attempted=%s", successful_calls, len(valid_phones))


    return {
        "attempted": len(valid_phones),
        "successful_calls": successful_calls,
        "results": call_results,
    }


def make_call(phone_number: str, message: str):
    contact = ParentContact(phone=phone_number)
    return trigger_twilio_ivr_calls(contacts=[contact], message=message)

