import os
import json
import boto3
from fastapi import Request, HTTPException
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware


class CognitoAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating Cognito JWT tokens.
    Loads JWKS keys from AWS Secrets Manager (no internet required).
    """

    def __init__(self, app):
        super().__init__(app)

        # --- Environment Variables ---
        self.region = os.getenv("COGNITO_REGION")
        self.audience = os.getenv("AUDIENCE")
        self.secret_name = os.getenv("JWKS_SECRET_NAME")

        if not self.region or not self.secret_name or not self.audience:
            raise Exception("❌ Missing required environment variables for Cognito verification.")

        # --- Load JWKS from Secrets Manager ---
        self.jwks = self._load_jwks_from_secrets_manager()
        if not self.jwks:
            raise Exception("❌ Failed to load JWKS keys from Secrets Manager.")

        # Optional log for verification (you can remove later)
        print("✅ Loaded JWKS key IDs:", [k.get("kid") for k in self.jwks])

    def _load_jwks_from_secrets_manager(self):
        """Load and safely decode JWKS from Secrets Manager."""
        try:
            sm = boto3.client("secretsmanager", region_name=self.region)
            secret = sm.get_secret_value(SecretId=self.secret_name)
            raw_secret = secret["SecretString"]

            # Try to parse once
            parsed = json.loads(raw_secret)

            # Handle double-encoded JSON (common issue)
            if isinstance(parsed, str):
                parsed = json.loads(parsed)

            keys = parsed.get("keys")
            if not keys:
                print("⚠️ JWKS secret does not contain 'keys' array.")
            return keys

        except Exception as e:
            print(f"❌ Failed to load or parse JWKS secret: {str(e)}")
            return None

    async def dispatch(self, request: Request, call_next):
        """Verify JWT token on each request."""
        auth_header = request.headers.get("Authorization")

        # --- Check header ---
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]

        try:
            # --- Decode header & find matching key ---
            header = jwt.get_unverified_header(token)
            key = next(k for k in self.jwks if k["kid"] == header["kid"])

            # --- Decode and verify JWT ---
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                options={"verify_exp": True}
            )

            token_use = payload.get("token_use")
            if token_use not in ("id", "access"):
                raise HTTPException(status_code=401, detail=f"Invalid token type: {token_use}")

            # --- Store payload in request.state ---
            request.state.user = payload

        except StopIteration:
            raise HTTPException(status_code=403, detail="Unknown KID — JWKS mismatch")
        except HTTPException:
            raise
        except Exception as e:
            # Any unexpected validation failure
            raise HTTPException(status_code=403, detail=f"Token validation failed: {str(e)}")

        # --- Continue with request ---
        return await call_next(request)
