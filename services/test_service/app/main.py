import os
import json
import boto3
import logging
import psycopg2
from fastapi import FastAPI
from mangum import Mangum  # ✅ required for AWS Lambda integration

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI(title="DB Connection Test Service")

@app.get("/")
def test_connection():
    try:
        region = os.environ["REGION"]
        secret_name = os.environ["DB_SECRET_NAME"]
        proxy_endpoint = os.environ["DB_PROXY_ENDPOINT"]

        logger.info(f"Testing DB connection in {region}")
        logger.info(f"Secret name: {secret_name}")
        logger.info(f"Proxy endpoint: {proxy_endpoint}")

        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        logger.info("✅ Secret fetched successfully")

        secret = json.loads(response["SecretString"])
        username = secret["username"]
        password = secret["password"]
        dbname = secret["dbname"]
        port = secret["port"]

        conn_str = f"host={proxy_endpoint} port={port} user={username} password={password} dbname={dbname}"

        logger.info("🔌 Connecting to DB...")
        conn = psycopg2.connect(conn_str, connect_timeout=5)
        logger.info("✅ Connection established")

        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        now = cur.fetchone()
        cur.close()
        conn.close()

        return {"status": "success", "timestamp": str(now)}

    except Exception as e:
        logger.exception("❌ DB test failed")
        return {"status": "error", "error": str(e)}

# ✅ This is the correct Lambda entry point
handler = Mangum(app)
