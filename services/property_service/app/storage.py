from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

import boto3


logger = logging.getLogger()


class S3AssetStorage:
    def __init__(self, bucket_name: str | None, presign_ttl_seconds: int = 3600, region_name: str | None = None) -> None:
        if not bucket_name:
            raise ValueError("Asset bucket name must be provided.")
        self.bucket_name = bucket_name
        self.presign_ttl_seconds = presign_ttl_seconds
        self.region_name = region_name
        self.s3_client = boto3.client("s3", region_name=region_name)

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        clean_prefix = prefix.strip().strip("/")
        if not clean_prefix:
            raise ValueError("Prefix cannot be empty.")
        return clean_prefix

    @staticmethod
    def _normalize_extension(extension: str | None) -> str | None:
        if not extension:
            return None
        ext = extension.strip().lstrip(".")
        return ext or None

    def generate_key(self, prefix: str, extension: str | None = None) -> str:
        clean_prefix = self._normalize_prefix(prefix)
        normalized_extension = self._normalize_extension(extension)
        key = f"{clean_prefix}/{uuid4()}"
        if normalized_extension:
            key = f"{key}.{normalized_extension}"
        return key

    def create_presigned_post(self, key: str, content_type: str) -> dict[str, Any]:
        if not content_type:
            raise ValueError("content_type is required to generate a pre-signed POST.")
        return self.s3_client.generate_presigned_post(
            Bucket=self.bucket_name,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[{"Content-Type": content_type}],
            ExpiresIn=self.presign_ttl_seconds,
        )

    def create_upload(self, prefix: str, content_type: str, extension: str | None = None) -> dict[str, Any]:
        key = self.generate_key(prefix, extension)
        try:
            payload = self.create_presigned_post(key, content_type)
        except Exception as exc:
            logger.error("Failed to generate pre-signed POST for key %s", key, exc_info=exc)
            raise
        payload["key"] = key
        return payload

    def create_read_url(self, key: str) -> str:
        try:
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=self.presign_ttl_seconds,
            )
        except Exception as exc:
            logger.error("Failed to generate pre-signed GET for key %s", key, exc_info=exc)
            raise
