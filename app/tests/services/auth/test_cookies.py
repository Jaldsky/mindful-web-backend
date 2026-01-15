from unittest import TestCase

from starlette.responses import Response

from app.config import (
    AUTH_COOKIE_HTTPONLY,
    AUTH_COOKIE_SECURE,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.services.auth.cookies import clear_auth_cookies, set_auth_cookies
from app.services.auth.constants import AUTH_ACCESS_COOKIE_NAME, AUTH_COOKIE_SAMESITE, AUTH_REFRESH_COOKIE_NAME


class TestSetAuthCookies(TestCase):
    def test_sets_access_and_refresh_cookies(self):
        response = Response()

        set_auth_cookies(response, "access-token", "refresh-token")

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 2)

        access_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_ACCESS_COOKIE_NAME}=")
        )
        refresh_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_REFRESH_COOKIE_NAME}=")
        )

        self.assertIn("access-token", access_cookie)
        self.assertIn("Path=/", access_cookie)
        self.assertIn(f"SameSite={AUTH_COOKIE_SAMESITE}", access_cookie)
        self.assertIn(f"Max-Age={JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60}", access_cookie)
        if AUTH_COOKIE_HTTPONLY:
            self.assertIn("HttpOnly", access_cookie)
        if AUTH_COOKIE_SECURE:
            self.assertIn("Secure", access_cookie)

        self.assertIn("refresh-token", refresh_cookie)
        self.assertIn("Path=/", refresh_cookie)
        self.assertIn(f"SameSite={AUTH_COOKIE_SAMESITE}", refresh_cookie)
        self.assertIn(f"Max-Age={JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60}", refresh_cookie)
        if AUTH_COOKIE_HTTPONLY:
            self.assertIn("HttpOnly", refresh_cookie)
        if AUTH_COOKIE_SECURE:
            self.assertIn("Secure", refresh_cookie)


class TestClearAuthCookies(TestCase):
    def test_clears_access_and_refresh_cookies(self):
        response = Response()

        clear_auth_cookies(response)

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 2)

        access_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_ACCESS_COOKIE_NAME}=")
        )
        refresh_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_REFRESH_COOKIE_NAME}=")
        )

        self.assertIn("Max-Age=0", access_cookie)
        self.assertIn("Max-Age=0", refresh_cookie)
