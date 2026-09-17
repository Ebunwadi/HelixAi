from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Header
from jwt import PyJWKClient

from helix_api.core.config import Settings, get_settings
from helix_api.core.errors import AuthenticationError
from helix_api.modules.auth.schemas import AuthenticatedIdentity

AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]
DevSubjectHeader = Annotated[str | None, Header(alias="X-Helix-Subject")]
DevEmailHeader = Annotated[str | None, Header(alias="X-Helix-Email")]
DevNameHeader = Annotated[str | None, Header(alias="X-Helix-Name")]


class JwtVerifier:
    def __init__(self, settings: Settings) -> None:
        if not all(
            [settings.helix_auth_issuer, settings.helix_auth_audience, settings.helix_auth_jwks_url]
        ):
            raise RuntimeError("JWT auth mode requires issuer, audience and JWKS URL")
        assert settings.helix_auth_jwks_url is not None
        self.settings = settings
        self.jwks_client = PyJWKClient(settings.helix_auth_jwks_url)

    def verify(self, token: str) -> AuthenticatedIdentity:
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.settings.helix_auth_audience,
            issuer=self.settings.helix_auth_issuer,
        )
        subject = claims.get("sub")
        if not subject:
            raise AuthenticationError("Token does not contain a subject")
        return AuthenticatedIdentity(
            subject=str(subject),
            email=claims.get("email") or claims.get("preferred_username"),
            display_name=claims.get("name"),
        )


@lru_cache
def get_jwt_verifier() -> JwtVerifier:
    return JwtVerifier(get_settings())


def authenticate_request(
    authorization: AuthorizationHeader = None,
    dev_subject: DevSubjectHeader = None,
    dev_email: DevEmailHeader = None,
    dev_name: DevNameHeader = None,
) -> AuthenticatedIdentity:
    settings = get_settings()

    if settings.helix_auth_mode == "dev":
        if not dev_subject:
            raise AuthenticationError(
                "Development auth requires the X-Helix-Subject header"
            )
        return AuthenticatedIdentity(
            subject=dev_subject,
            email=dev_email,
            display_name=dev_name,
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("A Bearer token is required")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        return get_jwt_verifier().verify(token)
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError("Bearer token validation failed") from exc
