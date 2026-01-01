"""
Middleware and request helpers for the API.
"""

from __future__ import annotations

import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from src.config import settings


def get_client_ip(request: Request) -> str:
    """
    Get the real client IP address, preventing spoofing via X-Forwarded-For.
    """
    client_host = (request.client.host if request.client else "") or ""

    if not settings.trust_proxy_headers:
        return client_host

    trusted = set([ip.strip() for ip in (settings.trusted_proxy_ips or set()) if ip and ip.strip()])
    trust_all = "*" in trusted
    if not (trust_all or client_host in trusted):
        # Do not trust forwarded headers from untrusted sources.
        return client_host

    xff = (request.headers.get("x-forwarded-for") or "").strip()
    if xff:
        return xff.split(",")[0].strip() or client_host
    xri = (request.headers.get("x-real-ip") or "").strip()
    return xri or client_host


def setup_compression(app: FastAPI) -> None:
    app.add_middleware(GZipMiddleware, minimum_size=800)


def setup_cors(app: FastAPI) -> None:
    cors_origins = list(settings.cors_allow_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        max_age=settings.cors_max_age,
    )


def setup_security_headers(app: FastAPI) -> None:
    def generate_csp_nonce() -> str:
        return secrets.token_urlsafe(16)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if settings.csp_use_nonce:
            nonce = generate_csp_nonce()
            response.headers["X-CSP-Nonce"] = nonce
            csp = (
                "default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )

        response.headers["Content-Security-Policy"] = csp
        return response


def setup_request_size_limit(app: FastAPI) -> None:
    @app.middleware("http")
    async def limit_request_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10_000_000:
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload too large"},
                headers={"Cache-Control": "no-store"},
            )
        return await call_next(request)
