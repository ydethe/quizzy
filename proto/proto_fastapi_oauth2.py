"""
FastAPI OAuth2 integration with Authentik using OpenID Connect
"""
import time
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import httpx
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeSerializer
from jose import jwt, jwk

from quizzy.config import config


class Token(BaseModel):
    access_token: str
    token_type: str
    userinfo: Optional[Dict[str, Any]] = None


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config.JWT_SECRET)

serializer = URLSafeSerializer(config.COOKIE_SECRET)

oauth = OAuth()
oauth.register(
    "authentik",
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    server_metadata_url=str(config.OPENID_CONFIG_URL),
    client_kwargs={"scope": "openid email"},
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Public endpoint"""
    return {"message": "FastAPI with Authentik OAuth2"}


@app.get("/auth/callback")
async def auth(request: Request) -> Dict[str, str]:
    token = await oauth.authentik.authorize_access_token(request)
    access_token: str = token["access_token"]

    # Store the token in a signed cookie
    response = RedirectResponse(url="/protected")
    response.set_cookie("access_token", serializer.dumps(access_token), httponly=True, secure=False)

    return response


@app.get("/login")
async def login(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for("auth")
    return await oauth.authentik.authorize_redirect(request, redirect_uri)


async def get_verified_claims(request: Request):
    cookie = request.cookies.get("access_token")
    if not cookie:
        raise HTTPException(status_code=401, detail="Missing token cookie")

    try:
        token = serializer.loads(cookie)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid cookie signature")

    # === Verify JWT signature and claims ===
    await oauth.authentik.load_server_metadata()
    jwks_url = oauth.authentik.server_metadata.get("jwks_uri")

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
            issuer=oauth.authentik.server_metadata.get("issuer"),
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token invalid: {e}")

    # Optional: check expiration
    if claims.get("exp") and time.time() > claims["exp"]:
        raise HTTPException(status_code=401, detail="Token expired")

    return claims


@app.get("/protected")
async def protected(user=Depends(get_verified_claims)):
    return {"message": "Access granted", "user": user}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
