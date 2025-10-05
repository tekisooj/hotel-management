import os
import json
import boto3
from fastapi import Request, HTTPException
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware


class CognitoAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for validating AWS Cognito JWT tokens."""

    def __init__(self, app):
        super().__init__(app)

        # --- Environment ---
        self.region = os.getenv("COGNITO_REGION")
        self.audience = os.getenv("AUDIENCE")
        self.secret_name = os.getenv("JWKS_SECRET_NAME")

        if not self.region or not self.secret_name or not self.audience:
            raise Exception("❌ Missing env vars: COGNITO_REGION, JWKS_SECRET_NAME, AUDIENCE")

        # --- Load JWKS ---
        self.jwks = self._load_jwks_from_secrets_manager()
        print(f"✅ JWKS loaded successfully ({len(self.jwks)} keys): {[k['kid'] for k in self.jwks]}")

    def _load_jwks_from_secrets_manager(self):
        """Retrieve JWKS secret from AWS Secrets Manager."""
        sm = boto3.client("secretsmanager", region_name=self.region)
        secret = sm.get_secret_value(SecretId=self.secret_name)

        raw = secret.get("SecretString")
        if not raw:
            raise Exception("SecretString is missing in JWKS secret")

        data = json.loads(raw)
        if not isinstance(data, dict) or "keys" not in data:
            raise Exception("JWKS secret must contain a 'keys' field")

        return data["keys"]

    async def dispatch(self, request: Request, call_next):
        """Validate Cognito JWT from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]

        try:
            header = jwt.get_unverified_header(token)
            token_kid = header.get("kid")
            if not token_kid:
                raise HTTPException(status_code=403, detail="Missing KID in token header")

            key = next(k for k in self.jwks if k["kid"] == token_kid)

            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                options={
                    "verify_exp": True,
                    "verify_at_hash": False  # ✅ Disable at_hash validation for ID tokens
                }
            )

            if payload.get("token_use") not in ("id", "access"):
                raise HTTPException(status_code=401, detail=f"Invalid token type: {payload.get('token_use')}")

            request.state.user = payload

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Token validation failed: {str(e)}")

        return await call_next(request)
