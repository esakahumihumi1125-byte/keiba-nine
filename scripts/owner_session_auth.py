"""Private owner login cookie: secure, signed, expiry-bounded; no session storage.

Supports the existing Basic auth as a fallback. A cookie is valid only for
this deployment's password and is revoked by password rotation.
"""
import hashlib
import hmac
import re
import time

COOKIE_NAME = "__Host-keiba-session"
SESSION_SECONDS = 7 * 24 * 60 * 60
_SESSION_CONTEXT = b"keiba-nine-private-session-v1:"


def owner_credentials_match(username, password, expected, configured_username):
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    if len(username) > 128 or len(password) > 2048:
        return False
    digest = hashlib.sha256((username + ":" + password).encode("utf-8")).digest()
    # Compare fixed-size hashes even for a nonexistent username.
    return hmac.compare_digest(digest, expected) and username == configured_username


def session_cookie(expected, now=None):
    issued = int(time.time() if now is None else now)
    expires = issued + SESSION_SECONDS
    message = _SESSION_CONTEXT + str(expires).encode("ascii")
    signature = hmac.new(expected, message, hashlib.sha256).hexdigest()
    return (f"{COOKIE_NAME}={expires}.{signature}; Path=/; Max-Age={SESSION_SECONDS}; "
            "HttpOnly; Secure; SameSite=Strict")


def session_cookie_valid(header, expected, now=None):
    if not isinstance(header, str) or len(header) > 4096:
        return False
    found = [chunk.strip()[len(COOKIE_NAME) + 1:]
             for chunk in header.split(";")
             if chunk.strip().startswith(COOKIE_NAME + "=")]
    if len(found) != 1:
        return False
    token = found[0]
    if not re.fullmatch(r"[0-9]{10,11}\.[a-f0-9]{64}", token):
        return False
    expires_s, signature = token.split(".", 1)
    current = int(time.time() if now is None else now)
    expires = int(expires_s)
    if not current < expires <= current + SESSION_SECONDS:
        return False
    good = hmac.new(expected, _SESSION_CONTEXT + expires_s.encode("ascii"),
                    hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, good)


def clear_session_cookie():
    return (f"{COOKIE_NAME}=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; "
            "HttpOnly; Secure; SameSite=Strict")
