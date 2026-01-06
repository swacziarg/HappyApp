# backend/auth/supabase.py
import requests
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

SUPABASE_PROJECT_ID = "orbgbbrltetcvbjpqsim"
SUPABASE_ISSUER = f"https://{SUPABASE_PROJECT_ID}.supabase.co/auth/v1"
JWKS_URL = f"{SUPABASE_ISSUER}/.well-known/jwks.json"

jwks = requests.get(JWKS_URL).json()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=SUPABASE_ISSUER,
        )
        return payload  # payload["sub"] = user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
