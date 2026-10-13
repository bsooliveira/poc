import secrets
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer = HTTPBearer(auto_error=False)


@lru_cache
def jwks_client():
    return jwt.PyJWKClient(
        f"https://login.microsoftonline.com/{settings().entra_tenant_id}/discovery/v2.0/keys",
        timeout=10,
    )


def identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    x_simplfaq: str = Header(default=""),
):
    cfg = settings()
    if cfg.auth_mode == "local":
        if x_simplfaq != "local-poc":
            raise HTTPException(401, "Cabeçalho de acesso local ausente")
        return {"id": "local-reviewer", "name": "Revisor da POC", "mode": "local"}
    if not credentials:
        raise HTTPException(
            401, "Autenticação necessária", headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    if cfg.auth_mode == "demo":
        if not secrets.compare_digest(token, cfg.demo_token):
            raise HTTPException(401, "Token de demonstração inválido")
        return {"id": "demo-local", "name": "Revisor local", "mode": "demo"}
    try:
        key = jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=cfg.entra_audience,
            issuer=f"https://login.microsoftonline.com/{cfg.entra_tenant_id}/v2.0",
            options={"require": ["exp", "iat", "nbf", "iss", "aud", "tid", "oid"]},
        )
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, "Token Entra ID inválido ou expirado") from None
    if (
        claims["tid"] != cfg.entra_tenant_id
        or cfg.entra_scope not in claims.get("scp", "").split()
    ):
        raise HTTPException(403, "Tenant ou escopo não autorizado")
    if cfg.entra_group_id not in claims.get("groups", []):
        raise HTTPException(
            403,
            "Grupo corporativo ausente; configure group claims também para usuários com overage",
        )
    return {
        "id": claims["oid"],
        "name": claims.get("name", claims["oid"]),
        "mode": "entra",
    }
