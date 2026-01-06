# backend/auth/supabase.py

import logging
import requests
from functools import lru_cache

from jose import jwt, jwk
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

SUPABASE_PROJECT_ID = "orbgbbrltetcvbjpqsim"
SUPABASE_ISSUER = f"https://{SUPABASE_PROJECT_ID}.supabase.co/auth/v1"
JWKS_URL = f"{SUPABASE_ISSUER}/.well-known/jwks.json"

security = HTTPBearer()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")

# -----------------------------------------------------------------------------
# JWKS handling
# -----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_jwks():
    resp = requests.get(JWKS_URL, timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_public_key(token: str):
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")


    jwks = get_jwks()

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwk.construct(key)


    # Supabase may have rotated keys — refresh once
    get_jwks.cache_clear()
    jwks = get_jwks()

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwk.construct(key)

    raise HTTPException(status_code=401, detail="Public key not found")


# -----------------------------------------------------------------------------
# FastAPI dependency
# -----------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing credentials")

    token = credentials.credentials
    try:
        public_key = get_public_key(token)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["ES256", "RS256"],
            issuer=SUPABASE_ISSUER,
            options={"verify_aud": False},
        )


        logger.info("Authenticated user %s", payload.get("sub"))
        return payload

    except Exception as e:
        logger.exception("Auth failed")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {str(e)}",
        )
