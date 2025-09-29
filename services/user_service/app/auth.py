import os
import json
import boto3
from fastapi import Request, HTTPException
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware

class CognitoAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.audience = os.getenv("AUDIENCE")
        self.region = os.getenv("COGNITO_REGION")
        self.secret_name = os.getenv("JWKS_SECRET_NAME")

        # ✅ Load JWKS from Secrets Manager instead of internet
        try:
            sm = boto3.client("secretsmanager", region_name=self.region)
            secret = sm.get_secret_value(SecretId=self.secret_name)
            self.jwks = json.loads(secret["SecretString"])["keys"]
        except Exception as e:
            raise Exception(f"Failed to load JWKS from Secrets Manager: {str(e)}")

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth.split(" ")[1]

        try:
            header = jwt.get_unverified_header(token)
            key = next(k for k in self.jwks if k["kid"] == header["kid"])
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                options={"verify_exp": True}
            )

            if payload.get("token_use") not in ("id", "access"):
                raise HTTPException(status_code=401, detail="Invalid token type")

            request.state.user = payload

        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Token validation failed: {str(e)}")

        return await call_next(request)
