"""Logging safety tests."""

import logging

from app.core.logging_config import SensitiveAccessLogFilter


def _uvicorn_access_record(request_target: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:1234", "GET", request_target, "1.1", 200),
        exc_info=None,
    )


def test_sensitive_access_log_filter_suppresses_google_callback_queries():
    access_filter = SensitiveAccessLogFilter()

    assert (
        access_filter.filter(
            _uvicorn_access_record(
                "/api/v1/auth/google/callback?code=authorization-code&state=poll-secret"
            )
        )
        is False
    )
    assert (
        access_filter.filter(
            _uvicorn_access_record(
                "/api/v1/sso/oauth/google/callback?code=legacy-code&state=legacy-state"
            )
        )
        is False
    )


def test_sensitive_access_log_filter_keeps_non_callback_requests():
    access_filter = SensitiveAccessLogFilter()

    assert access_filter.filter(_uvicorn_access_record("/api/v1/auth/google/authorize")) is True
    assert access_filter.filter(_uvicorn_access_record("/healthz")) is True
