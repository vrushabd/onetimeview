from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class SecretCreate(BaseModel):
    """Schema for creating a new secret"""
    content_type: str = Field(..., pattern="^(text|image|video|file)$")
    content: Optional[str] = None
    password: Optional[str] = None
    expiry_hours: Optional[int] = None  # Deprecated, prefer expiry_minutes
    expiry_minutes: Optional[int] = None # Minutes until expiration
    max_views: Optional[int] = Field(default=1, ge=1, le=100)  # Number of times secret can be viewed
    is_premium: bool = False
    webhook_url: Optional[str] = None  # Called once when the secret is viewed (burn notification)

    @field_validator('content')
    def validate_content(cls, v, info):
        if info.data.get('content_type') == 'text' and not v:
            raise ValueError('Content is required for text secrets')
        return v


class FileSecretCreate(BaseModel):
    """Schema for creating a secret from an already-uploaded file (storage-agnostic)"""
    content_type: str  # image, video, file (non-text only)
    file_name: str
    mime_type: Optional[str] = None
    cloud_url: str
    cloud_public_id: str
    cloud_resource_type: Optional[str] = None  # kept for DB compat, not required
    password: Optional[str] = None
    expiry_hours: Optional[int] = None
    expiry_minutes: Optional[int] = None
    max_views: Optional[int] = Field(default=1, ge=1, le=100)
    is_premium: bool = False
    webhook_url: Optional[str] = None  # Called once when the secret is viewed (burn notification)

# Keep old name as an alias for backward compatibility with older imports/routes.
CloudinarySecretCreate = FileSecretCreate


class SecretResponse(BaseModel):
    """Response after creating a secret"""
    id: str
    url: str
    expires_at: Optional[datetime]
    has_password: bool
    content_type: str
    max_views: int
    
    class Config:
        from_attributes = True


class SecretView(BaseModel):
    """Response when viewing a secret"""
    content_type: str
    content: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    download_url: Optional[str] = None
    view_url: Optional[str] = None
    remaining_views: Optional[int] = None
    
    class Config:
        from_attributes = True


class PasswordVerify(BaseModel):
    """Schema for password verification"""
    password: str


class ReportCreate(BaseModel):
    """Schema for submitting a bug/issue report"""
    page: str = Field(..., min_length=1, max_length=100, description="Page or component with the issue")
    issue_type: str = Field(..., pattern="^(create|view|file_upload|expired|navigation|performance|other)$")
    description: str = Field(..., min_length=10, max_length=2000, description="Description of the problem")
    contact_email: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = Field(default=None, max_length=500)
    user_agent: Optional[str] = Field(default=None, max_length=500)


class ReportResponse(BaseModel):
    """Response after submitting a report"""
    id: str
    status: str
    message: str
