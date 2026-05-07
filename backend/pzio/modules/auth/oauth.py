from authlib.integrations.starlette_client import OAuth
from pzio.config import settings

oauth = OAuth()

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    api_base_url="https://api.github.com/",
    access_token_url="https://github.com/login/oauth/access_token",
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    client_kwargs={"scope": "user:email"},
)