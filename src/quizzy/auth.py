import requests
import datetime  # to calculate expiration of the JWT

from typing import Any, Union
from httpx import AsyncClient
from fastapi_sso.sso.base import DiscoveryDocument, OpenID
from fastapi_sso.sso.generic import create_provider
from fastapi import APIRouter, HTTPException, Security, Request
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyCookie  # this is the part that puts the lock icon to the docs

from jose import jwt  # pip install python-jose[cryptography]

from .config import config

auth_router = APIRouter(prefix="/auth")


class RequiresLoginException(HTTPException):
    pass


def convert_openid(response: dict[str, Any], _client: Union[AsyncClient, None]) -> OpenID:
    """Convert user information returned by OIDC"""
    print(response)
    return OpenID(display_name=response["sub"])


def load_discovery_document(oid_url: str) -> DiscoveryDocument:
    ret = requests.get(oid_url)
    dat = ret.json()
    doc = DiscoveryDocument(
        {
            "authorization_endpoint": str(dat["authorization_endpoint"]),
            "token_endpoint": str(dat["token_endpoint"]),
            "userinfo_endpoint": str(dat["userinfo_endpoint"]),
        }
    )
    return doc


discovery_document = load_discovery_document(str(config.OPENID_CONFIG_URL))

GenericSSO = create_provider(
    name="oidc", discovery_document=discovery_document, response_convertor=convert_openid
)

sso = GenericSSO(
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    redirect_uri=config.REDIRECT_URI,
    allow_insecure_http=True,
)


async def get_logged_user(cookie: str = Security(APIKeyCookie(name="token"))) -> OpenID:
    """Get user's JWT stored in cookie 'token', parse it and return the user's OpenID."""
    print("toto")
    try:
        claims = jwt.decode(cookie, key=config.JWT_SECRET, algorithms=["HS256"])
        print(claims)
        return OpenID(**claims["pld"])
    except Exception as error:
        raise RequiresLoginException(
            status_code=401, detail="Invalid authentication credentials"
        ) from error


# @auth_router.get("/protected")
# async def protected_endpoint(user: OpenID = Depends(get_logged_user)):
#     """This endpoint will say hello to the logged user.
#     If the user is not logged, it will return a 401 error from `get_logged_user`."""
#     return {
#         "message": f"You are very welcome, {user.email}!",
#     }


@auth_router.get("/login")
async def login():
    """Redirect the user to the Google login page."""
    async with sso:
        return await sso.get_login_redirect()


@auth_router.get("/logout")
async def logout():
    """Forget the user's session."""
    response = RedirectResponse(url="/protected")
    response.delete_cookie(key="token")
    return response


@auth_router.get("/callback")
async def login_callback(request: Request):
    """Process login and redirect the user to the protected endpoint."""
    async with sso:
        openid = await sso.verify_and_process(request)
        if not openid:
            raise HTTPException(status_code=401, detail="Authentication failed")
    # Create a JWT with the user's OpenID
    expiration = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1)
    token = jwt.encode(
        {"pld": openid.dict(), "exp": expiration, "sub": openid.id},
        key=config.JWT_SECRET,
        algorithm="HS256",
    )
    response = RedirectResponse(url="/protected")
    response.set_cookie(
        key="token", value=token, expires=expiration
    )  # This cookie will make sure /protected knows the user
    return response
