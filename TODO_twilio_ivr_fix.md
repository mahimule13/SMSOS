# TODO - Twilio IVR RuntimeError Fix

- [ ] Confirm where Twilio env vars are expected (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_PHONE_NUMBER)
- [ ] Patch `schoolms/settings.py` to read correct env var names (not using the error hashes as keys)
- [ ] Add safer fallback/error message in `apps/accounts/ivr_service.py` to report missing settings
- [ ] Restart Django and retry POST `/fee-pending-calls/`
- [ ] Verify calls are created / failures are logged

