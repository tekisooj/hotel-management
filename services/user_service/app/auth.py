import os
from fastapi import Request, HTTPException
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
import requests

class CognitoAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.cognito_region = os.getenv("COGNITO_REGION", None)
        self.user_pool_id = os.getenv("USER_POOL_ID", None)
        self.audience = os.getenv("AUDIENCE", None)
        self.jwks_url = os.getenv("JWKS_URL", None)
        if not self.jwks_url or not self.audience:
            raise Exception("Cognito data not properly set")
        self.jwks = requests.get(self.jwks_url).json()["keys"]

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth.split(" ")[1]
        try:
            header = jwt.get_unverified_header(token)
            key = next(k for k in self.jwks if k["kid"] == header["kid"])
            payload = jwt.decode(token, key, algorithms=["RS256"], audience=self.audience)
            request.state.user = payload
        except Exception as e:
            raise HTTPException(status_code=403, detail="Token validation failed")

        return await call_next(request)
