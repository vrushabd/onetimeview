from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from datetime import datetime
import uuid
from backend.database import Base


import secrets
import string

def generate_short_id(length=12):
    """Generate a URL-safe short ID"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class Secret(Base):
    """Model for storing secrets with one-time view logic"""
    __tablename__ = "secrets"

    id = Column(String(36), primary_key=True, default=lambda: generate_short_id(length=6))
    content_type = Column(String(20), nullable=False)  # text, image, video, file
    content = Column(Text, nullable=True)  # For text secrets
    file_path = Column(String(255), nullable=True)  # Legacy local file path
    file_name = Column(String(255), nullable=True)  # Original filename
    mime_type = Column(String(100), nullable=True)  # MIME type for files
    password_hash = Column(String(100), nullable=True)  # Bcrypt hash if password protected
    expiry_time = Column(DateTime, nullable=True)  # Time-based expiration
    view_count = Column(Integer, default=0)  # Track number of views
    max_views = Column(Integer, default=1)  # Maximum allowed views (default 1)
    is_premium = Column(Boolean, default=False)  # Premium feature flag
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Cloudinary fields
    cloud_url = Column(String(500), nullable=True)  # Cloudinary secure URL
    cloud_public_id = Column(String(255), nullable=True)  # Cloudinary public_id for deletion
    cloud_resource_type = Column(String(20), nullable=True)  # image, video, raw
    
    def is_expired(self):
        """Check if secret has expired"""
        if self.view_count >= self.max_views:
            return True
        if self.expiry_time and datetime.utcnow() > self.expiry_time:
            return True
        return False
    

