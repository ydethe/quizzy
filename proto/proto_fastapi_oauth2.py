"""
FastAPI OAuth2 integration with Authentik using OpenID Connect
"""
import time
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import httpx
from pydantic import BaseModel, AnyHttpUrl
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeSerializer
from jose import jwt, jwk

from quizzy.config import config


class Claim(BaseModel):
    # {"iss":"https://authentik.johncloud.fr/application/o/quizzy/","sub":"f4d0408eef53ec3f660da2d77ded879af3d9278959c65974f5c0c24adb2aec2e","aud":"KW4rMxu2KXzm1yeq3kGctrZH2JiaU9IiIrNxYhm0","exp":1760006282,"iat":1760005982,"auth_time":1759910087,"acr":"goauthentik.io/providers/oauth2/default","amr":["pwd"],"nonce":"TUhvsWQOOEznKRehhy8L","sid":"2a34e1c4c97c1732fdba7b630aef8a74f478ba8d5159a8d8491abd5e8d183d83","email":"ydethe@gmail.com","email_verified":true,"azp":"KW4rMxu2KXzm1yeq3kGctrZH2JiaU9IiIrNxYhm0","uid":"eUf4bK6XBHWMVjH015SJ7l8Yxb5isa7uQEmTX5ff"}}
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


async def get_verified_claims(request: Request) -> Claim:
    cookie = request.cookies.get("access_token")
    if not cookie:
        raise HTTPException(status_code=401, detail="Missing token cookie")

    try:
        token = serializer.loads(cookie)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid cookie signature")

    # === Verify JWT signature and claims ===
    await oauth.authentik.load_server_metadata()
    jwks_url: str = oauth.authentik.server_metadata.get("jwks_uri")

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

    py_claims = Claim.model_validate(claims)

    return py_claims


@app.get("/protected")
async def protected(user: Claim = Depends(get_verified_claims)):
    return {"message": "Access granted", "user": user}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
