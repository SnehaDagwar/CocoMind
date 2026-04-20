"""RBAC middleware — require_role decorator for FastAPI routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from src.audit.chain import write_record
from src.models.auth import Permission, Role, User


def _get_current_user(request: Request) -> User:
    """Extract current user from request.

    Tier-1: Simple header-based auth for demo.
    Tier-2: OIDC/MeriPehchaan.
    """
    user_id = request.headers.get("X-User-ID", "demo-user")
    user_role = request.headers.get("X-User-Role", "Evaluator")

    try:
        role = Role(user_role)
    except ValueError:
        role = Role.EVALUATOR

    return User(
        user_id=user_id,
        name=request.headers.get("X-User-Name", "Demo User"),
        email=request.headers.get("X-User-Email", ""),
        role=role,
    )


def require_role(*roles: Role):
    """FastAPI dependency that enforces role-based access.

    Usage:
        @app.get("/api/vtm", dependencies=[Depends(require_role(Role.EVALUATOR))])
    """
    def dependency(request: Request) -> User:
        user = _get_current_user(request)

        if user.role not in roles:
            # Log denied attempt to audit chain
            write_record("ACCESS_DENIED", {
                "user_id": user.user_id,
                "role": user.role.value,
                "required_roles": [r.value for r in roles],
                "path": str(request.url.path),
                "method": request.method,
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role.value} not authorized. Required: {[r.value for r in roles]}",
            )

        return user

    return Depends(dependency)


def require_permission(permission: Permission):
    """FastAPI dependency that enforces permission-based access."""
    def dependency(request: Request) -> User:
        user = _get_current_user(request)

        if not user.has_permission(permission):
            write_record("ACCESS_DENIED", {
                "user_id": user.user_id,
                "role": user.role.value,
                "required_permission": permission.value,
                "path": str(request.url.path),
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' required.",
            )

        return user

    return Depends(dependency)
