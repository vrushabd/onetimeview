import bcrypt
import re
import os
import uuid
from pathlib import Path


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def sanitize_text(text: str, max_length: int = 50000) -> str:
    """Sanitize text input to prevent XSS and injection attacks"""
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove potentially dangerous HTML tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    return text


def sanitize_filename(filename: str) -> str:
    """Generate a secure random filename while preserving extension"""
    if not filename:
        return str(uuid.uuid4())
    
    # Get file extension
    ext = Path(filename).suffix.lower()
    
    # Validate extension
    allowed_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
        '.mp4', '.webm', '.mov',  # Videos
        '.pdf', '.zip', '.docx', '.txt', '.doc', '.xlsx', '.pptx'  # Files
    }
    
    if ext not in allowed_extensions:
        ext = '.bin'
    
    # Generate random filename
    random_name = str(uuid.uuid4())
    return f"{random_name}{ext}"


def get_mime_type(filename: str) -> str:
    """Get MIME type based on file extension"""
    ext = Path(filename).suffix.lower()
    
    mime_types = {
        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        # Videos
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        # Documents
        '.pdf': 'application/pdf',
        '.zip': 'application/zip',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.txt': 'text/plain',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }
    
    return mime_types.get(ext, 'application/octet-stream')


def validate_file_type(filename: str) -> tuple[bool, str]:
    """Validate if file type is allowed"""
    ext = Path(filename).suffix.lower()
    
    allowed = {
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        # Videos
        '.mp4', '.webm', '.mov',
        # Documents
        '.pdf', '.zip', '.docx', '.doc', '.txt', '.xlsx', '.pptx'
    }
    
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        return True, 'image'
    elif ext in {'.mp4', '.webm', '.mov'}:
        return True, 'video'
    elif ext in allowed:
        return True, 'file'
    
    return False, ''
