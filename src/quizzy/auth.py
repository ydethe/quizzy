from fastapi import Request, Depends, HTTPException

from . import logger


class AuthUser:
    def __init__(self, request: Request):
        self.username = request.headers.get("X-Authentik-Username", "")
        self.email = request.headers.get("X-Authentik-Email", "")
        self.name = request.headers.get("X-Authentik-Name", "")
        self.uid = request.headers.get("X-Authentik-Uid", "")
        self.groups = (
            request.headers.get("X-Authentik-Groups", "").split("|")
            if request.headers.get("X-Authentik-Groups")
            else []
        )
        self.jwt = request.headers.get("X-Authentik-Jwt", "")

    def is_authenticated(self) -> bool:
        return bool(self.username and self.uid)

    def has_group(self, group_name: str) -> bool:
        return group_name in self.groups

    def __repr__(self):
        return f"<AuthUser username={self.username} email={self.email}>"


def get_current_user(request: Request) -> AuthUser:
    """Dependency to extract authenticated user from Authentik headers"""
    user = AuthUser(request)
    if not user.is_authenticated():
        logger.warning("Unauthenticated request reached application")
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_group(group_name: str):
    """Dependency factory for group-based authorization"""

    def check_group(user: AuthUser = Depends(get_current_user)):
        if not user.has_group(group_name):
            raise HTTPException(
                status_code=403, detail=f"Access denied. Required group: {group_name}"
            )
        return user

    return check_group
