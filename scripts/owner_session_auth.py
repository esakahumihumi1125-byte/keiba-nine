"""Private owner login cookie: secure, signed, expiry-bounded; no session storage.

Supports the existing Basic auth as a fallback.
Lax permits iPhone Safari top-level navigation following cross-site opens and
login redirects; cookies remain Secure/HttpOnly/host-only with a random
browser-bound login form token and fetch-metadata checks. A cookie is valid only for
this deployment's password and is revoked by password rotation.
"""
import hashlib
import hmac
import re
import secrets
import time

COOKIE_NAME = "__Host-keiba-session"
SESSION_SECONDS = 7 * 24 * 60 * 60
_SESSION_CONTEXT = b"keiba-nine-private-session-v1:"



# A separate short-lived, random browser-bound form token prevents login CSRF
# without relying on Origin headers rewritten by Render / mobile browsers.
# The form token does not grant access; password verification is still required.
LOGIN_CSRF_COOKIE_NAME = "__Host-keiba-login-form"
LOGIN_CSRF_SECONDS = 30 * 60


def new_login_form_csrf():
    token = secrets.token_urlsafe(32)
    cookie = (f"{LOGIN_CSRF_COOKIE_NAME}={token}; Path=/; "
              f"Max-Age={LOGIN_CSRF_SECONDS}; HttpOnly; Secure; SameSite=Lax")
    return token, cookie


def login_form_csrf_valid(header, supplied):
    if not isinstance(supplied, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", supplied):
        return False
    if not isinstance(header, str) or len(header) > 4096:
        return False
    values = [part.strip()[len(LOGIN_CSRF_COOKIE_NAME) + 1:]
              for part in header.split(";")
              if part.strip().startswith(LOGIN_CSRF_COOKIE_NAME + "=")]
    return len(values) == 1 and hmac.compare_digest(values[0], supplied)


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
            "HttpOnly; Secure; SameSite=Lax")


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
            "HttpOnly; Secure; SameSite=Lax")
