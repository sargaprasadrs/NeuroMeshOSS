"""Shared FastAPI dependencies for authentication and authorization."""

from uuid import UUID
from fastapi import HTTPException, Request, status


def require_authenticated_user(request: Request) -> UUID:
    """Dependency that enforces JWT authentication and returns the user ID.

    Raises 401 if no valid token was provided.
    """
    user_payload = getattr(request.state, "user", None)
    if not user_payload or "sub" not in user_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UUID(user_payload["sub"])
