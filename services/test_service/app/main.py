import os
import json
import boto3
import logging
import psycopg2
from fastapi import FastAPI, HTTPException
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI(title="DB Connection Test Service")

@app.get("/")
def test_connection():
    try:
        region = os.getenv("REGION")
        secret_name = os.getenv("DB_SECRET_NAME")
        proxy_endpoint = os.getenv("DB_PROXY_ENDPOINT")

        if not all([region, secret_name, proxy_endpoint]):
            raise HTTPException(
                status_code=500,
                detail="Missing REGION, DB_SECRET_NAME, or DB_PROXY_ENDPOINT environment variables."
            )

        logger.info(f"🔍 Testing DB connection in region: {region}")
        logger.info(f"🔐 Secret name: {secret_name}")
        logger.info(f"🌐 Proxy endpoint: {proxy_endpoint}")

        client = boto3.client("secretsmanager", region_name=region, config=boto3.session.Config(connect_timeout=3, read_timeout=3))
        response = client.get_secret_value(SecretId=secret_name)
        logger.info("✅ Secret fetched successfully")

        secret = json.loads(response["SecretString"])
        username = secret["username"]
        password = secret["password"]
        dbname = secret["dbname"]
        port = secret["port"]

        conn_str = f"host={proxy_endpoint} port={port} user={username} password={password} dbname={dbname}"

        logger.info("🔌 Attempting to connect to PostgreSQL via RDS Proxy...")
        conn = psycopg2.connect(conn_str, connect_timeout=5)
        logger.info("✅ Connection established successfully")

        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        now = cur.fetchone()
        cur.close()
        conn.close()

        return {"status": "success", "timestamp": str(now)}

    except Exception as e:
        logger.exception("❌ DB test failed")
        return {"status": "error", "error": str(e)}

# ✅ Wrap FastAPI for Lambda (fixes missing 'send' error)
handler = Mangum(app, lifespan="off")
