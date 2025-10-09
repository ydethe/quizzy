"""
FastAPI OAuth2 integration with Authentik using OpenID Connect
"""
import time
from typing import List

from fastapi import HTTPException, Request
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
import httpx
from pydantic import BaseModel, AnyHttpUrl
from itsdangerous import URLSafeSerializer
from jose import jwt, jwk

from .config import config


class Claim(BaseModel):
    iss: AnyHttpUrl
    sub: str
    aud: str
    exp: int
    iat: int
    auth_time: int
    acr: str
    amr: List[str]
    nonce: str
    sid: str
    email: str
    email_verified: bool
    azp: str
    uid: str


cookie_serializer = URLSafeSerializer(config.COOKIE_SECRET)

oauth = OAuth()
oidc_client: StarletteOAuth2App = oauth.register(  # type: ignore
    "oidc_client",
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    server_metadata_url=str(config.OPENID_CONFIG_URL),
    client_kwargs={"scope": "openid email"},
)


async def get_verified_claims(request: Request) -> Claim:
    cookie = request.cookies.get("access_token")
    if not cookie:
        raise HTTPException(status_code=401, detail="Missing token cookie")

    try:
        token = cookie_serializer.loads(cookie)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid cookie signature")

    # === Verify JWT signature and claims ===
    await oidc_client.load_server_metadata()
    jwks_url: str = oidc_client.server_metadata.get("jwks_uri")

    async with httpx.AsyncClient() as client:
        jwks = (await client.get(jwks_url)).json()["keys"]

    header = jwt.get_unverified_header(token)
    key = next((k for k in jwks if k["kid"] == header["kid"]), None)
    if not key:
        raise HTTPException(status_code=401, detail="Unknown key ID")

    # Build public key
    public_key = jwk.construct(key)

    try:
        claims = jwt.decode(
            token,
            key=public_key.to_pem().decode(),
            algorithms=[key["alg"]],
            audience=config.CLIENT_ID,
            issuer=oidc_client.server_metadata.get("issuer"),
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token invalid: {e}")

    # Optional: check expiration
    if claims.get("exp") and time.time() > claims["exp"]:
        raise HTTPException(status_code=401, detail="Token expired")

    py_claims = Claim.model_validate(claims)

    return py_claims
