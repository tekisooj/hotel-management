from pydantic import BaseModel, Field


class AssetUploadRequest(BaseModel):
    prefix: str = Field(description="Folder prefix where the asset will be stored")
    content_type: str = Field(description="Content type of the asset to upload")
    extension: str | None = Field(default=None, description="Optional file extension to append to the key")


class AssetUploadResponse(BaseModel):
    key: str = Field(description="Generated S3 object key")
    upload_url: str = Field(description="Pre-signed URL to upload the asset")
    fields: dict[str, str] = Field(default_factory=dict, description="Form fields for the POST upload")
