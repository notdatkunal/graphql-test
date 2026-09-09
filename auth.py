import os

import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient, PyJWKError
from strawberry.permission import BasePermission

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
REALM = os.getenv("KEYCLOAK_REALM", "graphql-demo")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "graphql-app")

JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"

_jwks_client = PyJWKClient(JWKS_URL, cache_keys=True)

# Roles Keycloak adds to every token that we should never treat as app roles
_HELPER_ROLES = {"offline_access", "uma_authorization"}


def decode_token(token: str) -> dict:
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=[signing_key.algorithm_name],
        options={"verify_aud": False},
    )


def extract_roles(claims: dict) -> list[str]:
    roles = set(claims.get("realm_access", {}).get("roles", []))
    resource_roles = (
        claims.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", []) or []
    )
    roles.update(resource_roles)
    return sorted(
        r
        for r in roles
        if r not in _HELPER_ROLES and not r.startswith("default-roles-")
    )


def context_from_request(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth_header.removeprefix("Bearer ")
    try:
        claims = decode_token(token)
    except (PyJWKError, jwt.DecodeError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from exc
    return {
        "username": claims.get("preferred_username"),
        "roles": extract_roles(claims),
    }


class HasAnyRole(BasePermission):
    """Grant access if the authenticated user has at least one of `roles`."""

    roles: list[str] = []
    message: str | None = "Access denied"

    def has_permission(self, source, info, **kwargs) -> bool:
        roles = set(info.context.get("roles") if info.context else [])
        return bool(roles & set(self.roles))


class IsAdminOrHR(HasAnyRole):
    roles = ["ADMIN", "HR"]
    message = "Requires role(s): ADMIN, HR"