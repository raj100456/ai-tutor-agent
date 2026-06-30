"""
FastAPI dependency injection — auth, settings, user resolution.

Auth is configurable via config.yaml → security.auth_mode:
  none     — no auth (dev/local)
  api_key  — X-API-Key header
  clerk    — Clerk JWT Bearer token
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config.settings import get_settings

logger = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    """
    Resolve the current user based on the configured auth_mode.
    Returns a dict with at least {"id": str}.
    Raise HTTP 401 if auth is required and credentials are invalid.
    """
    settings = get_settings()
    mode = settings.auth_mode

    if mode == "none":
        return {"id": "local-user", "email": "local@localhost", "role": "dev"}

    if mode == "api_key":
        return _verify_api_key(x_api_key, settings)

    if mode == "clerk":
        return await _verify_clerk_jwt(credentials, settings)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unknown auth_mode '{mode}' in config.yaml → security.",
    )


def _verify_api_key(api_key: str | None, settings: Any) -> dict[str, Any]:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
        )
    raw_keys = settings.security.get("api_keys", "")
    valid_keys = {k.strip() for k in raw_keys.split(",") if k.strip()}
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return {"id": f"apikey-{api_key[:8]}", "role": "user"}


async def _verify_clerk_jwt(
    credentials: HTTPAuthorizationCredentials | None, settings: Any
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required.",
        )
    token = credentials.credentials
    clerk_cfg = settings.security.get("clerk", {})
    jwks_url = clerk_cfg.get("jwks_url", "https://api.clerk.com/v1/jwks")

    try:
        import httpx
        from jose import JWTError, jwk, jwt

        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            jwks = resp.json()

        # Decode without verification first to get key id
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token key.")

        public_key = jwk.construct(key_data)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return {
            "id": payload.get("sub", "unknown"),
            "email": payload.get("email", ""),
            "role": "user",
        }
    except Exception as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc
