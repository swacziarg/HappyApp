## backend/auth/supabase.py
import requests
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

SUPABASE_PROJECT_ID = "orbgbbrltetcvbjpqsim"
SUPABASE_ISSUER = f"https://{SUPABASE_PROJECT_ID}.supabase.co/auth/v1"
JWKS_URL = f"{SUPABASE_ISSUER}/.well-known/jwks.json"

jwks = requests.get(JWKS_URL).json()

def get_public_key(token: str):
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    for key in jwks["keys"]:
        if key["kid"] == kid:
            return key

    raise HTTPException(status_code=401, detail="Public key not found")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    print(jwt.get_unverified_claims(token))
    try:
        public_key = get_public_key(token)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=SUPABASE_ISSUER,
            options={
                "verify_aud": False,  
            },
        )

        return payload  # payload["sub"] is the user ID

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {str(e)}",
        )
