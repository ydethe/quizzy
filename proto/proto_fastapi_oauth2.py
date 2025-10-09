"""
FastAPI OAuth2 integration with Authentik using OpenID Connect
"""
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from quizzy.config import config


class Token(BaseModel):
    access_token: str
    token_type: str
    userinfo: Optional[Dict[str, Any]] = None


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config.JWT_SECRET)

oauth = OAuth()
oauth.register(
    "descope",
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    server_metadata_url=str(config.OPENID_CONFIG_URL),
    client_kwargs={"scope": "openid email"},
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Public endpoint"""
    return {"message": "FastAPI with Authentik OAuth2"}


@app.get("/auth/callback", response_model=Token)
async def auth(request: Request) -> Dict[str, str]:
    token = await oauth.descope.authorize_access_token(request)
    print(token)
    # userinfo = await oauth.descope.parse_id_token(request, token)
    # token["userinfo"] = userinfo
    return token


@app.get("/login")
async def login(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for("auth")
    return await oauth.descope.authorize_redirect(request, redirect_uri)


# def get_current_user(token: str = Depends(...)):
#     # We skip details; you can extract the Authorization header,
#     # Then decode & validate JWT (signature, issuer, audience, scopes) using PyJWT
#     # Or use Descope’s SDK to validate session / token.
#     # E.g., using DescopeClient.validate_session
#     from descope import DescopeClient
#     dc = DescopeClient(project_id=os.getenv("DESCOPE_PROJECT_ID"))
#     try:
#         auth_info = dc.validate_session(session_token=token)
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#     # Optionally check scopes or claims
#     return auth_info

# @app.get("/protected")
# async def protected_route(current = Depends(get_current_user)):
#     return {"hello": "protected data", "user": current}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
