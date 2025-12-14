from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class SecretCreate(BaseModel):
    """Schema for creating a new secret"""
    content_type: str = Field(..., pattern="^(text|image|video|file)$")
    content: Optional[str] = None
    password: Optional[str] = None
    expiry_hours: Optional[int] = None  # Hours until expiration
    max_views: Optional[int] = Field(default=1, ge=1, le=10)  # Number of times secret can be viewed
    is_premium: bool = False
    
    @field_validator('content')
    def validate_content(cls, v, info):
        if info.data.get('content_type') == 'text' and not v:
            raise ValueError('Content is required for text secrets')
        return v


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
    remaining_views: Optional[int] = None
    
    class Config:
        from_attributes = True


class PasswordVerify(BaseModel):
    """Schema for password verification"""
    password: str
