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

    print("🔑 TOKEN KID:", kid)

    jwks = get_jwks()
    print("🔑 JWKS KEYS:", [k.get("kid") for k in jwks.get("keys", [])])

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            print("✅ MATCHED KID")
            return jwk.construct(key)

    print("❌ KID NOT FOUND — refreshing JWKS")

    # Supabase may have rotated keys — refresh once
    get_jwks.cache_clear()
    jwks = get_jwks()
    print("🔁 JWKS KEYS AFTER REFRESH:", [k.get("kid") for k in jwks.get("keys", [])])

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            print("✅ MATCHED KID AFTER REFRESH")
            return jwk.construct(key)

    print("❌ STILL NO MATCHING KID")
    raise HTTPException(status_code=401, detail="Public key not found")


# -----------------------------------------------------------------------------
# FastAPI dependency
# -----------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    print("🔐 ENTERED get_current_user")

    if credentials is None:
        print("❌ NO CREDENTIALS")
        raise HTTPException(status_code=401, detail="Missing credentials")

    print("✅ AUTH SCHEME:", credentials.scheme)
    print("✅ TOKEN (first 20 chars):", credentials.credentials[:20])

    token = credentials.credentials
    print("🔐 Decoding token...")

    try:
        public_key = get_public_key(token)
        print("✅ Got public key")

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=SUPABASE_ISSUER,
            options={"verify_aud": False},
        )

        print("✅ DECODE SUCCESS")
        print("👤 USER SUB:", payload.get("sub"))

        logger.info("Authenticated user %s", payload.get("sub"))
        return payload

    except Exception as e:
        print("❌ JWT DECODE FAILED:", repr(e))
        logger.exception("Auth failed")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {str(e)}",
        )
