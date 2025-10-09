"""
FastAPI OAuth2 integration with Authentik using OpenID Connect
"""
from typing import Any, Dict

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from quizzy.config import config
from quizzy.auth import get_verified_claims, oidc_client, Claim, cookie_serializer


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config.JWT_SECRET)


@app.get("/")
async def root() -> Dict[str, str]:
    """Public endpoint"""
    return {"message": "FastAPI with Authentik OAuth2"}


@app.get("/auth/callback")
async def auth(request: Request) -> RedirectResponse:
    token: Dict[str, str] = await oidc_client.authorize_access_token(request)
    access_token: str = token["access_token"]

    # Store the token in a signed cookie
    response = RedirectResponse(url="/protected")
    response.set_cookie(
        "access_token", cookie_serializer.dumps(access_token), httponly=True, secure=False
    )

    return response


@app.get("/login")
async def login(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for("auth")
    return await oidc_client.authorize_redirect(request, redirect_uri)


@app.get("/protected")
async def protected(user: Claim = Depends(get_verified_claims)) -> Dict[str, Any]:
    return {"message": "Access granted", "user": user}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
