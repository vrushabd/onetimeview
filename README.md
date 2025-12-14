# OneTimeView – Secure One-Time Message & File Sharing

A production-ready web application for sharing secrets (text, images, videos, files) that self-destruct after being viewed once.

## 🌟 Features

- **One-Time View**: Content is automatically deleted after first view
- **Multiple Content Types**: Text, images, videos, and files
- **Password Protection**: Optional password security (Premium)
- **Time-Based Expiration**: Content expires after set time or first view
- **No Login Required**: Free tier requires no registration
- **SEO Optimized**: All pages with comprehensive meta tags
- **Mobile Responsive**: Works perfectly on all devices
- **Rate Limited**: Protection against abuse
- **Secure**: HTTPS-ready, bcrypt password hashing, input sanitization

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. **Clone or navigate to the repository**
```bash
cd /Users/vrushabhdadabaravkar/onetime
```

2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. **Run the application**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the application**
```
Open your browser to: http://localhost:8000
```

## 📁 Project Structure

```
onetime/
├── backend/
│   ├── main.py           # FastAPI application and routes
│   ├── models.py         # SQLAlchemy database models
│   ├── database.py       # Database configuration
│   ├── schemas.py        # Pydantic schemas for validation
│   ├── security.py       # Security utilities (hashing, sanitization)
│   └── cleanup.py        # Background cleanup task
├── frontend/
│   ├── index.html        # Home page
│   ├── create.html       # Create secret page
│   ├── view.html         # View secret page
│   ├── expired.html      # Expired/already viewed page
│   ├── privacy.html      # Privacy policy
│   ├── terms.html        # Terms of service
│   └── styles.css        # Custom CSS
├── uploads/              # File storage directory
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md            # This file
```

## 🔧 Configuration

Edit the `.env` file to configure:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: Secret key for security features
- `MAX_FILE_SIZE_FREE`: Max file size for free users (bytes)
- `MAX_FILE_SIZE_PREMIUM`: Max file size for premium users (bytes)
- `UPLOAD_DIR`: Directory for file uploads
- `RATE_LIMIT_PER_MINUTE`: Rate limit per IP address
- `ALLOWED_ORIGINS`: CORS allowed origins

## 📡 API Documentation

### Create Secret
```http
POST /api/secrets
Content-Type: multipart/form-data

Fields:
- content_type: "text" | "image" | "video" | "file"
- content: string (for text secrets)
- file: File (for file-based secrets)
- password: string (optional, premium)
- expiry_hours: number (optional, premium)
- is_premium: boolean

Response:
{
  "id": "uuid",
  "url": "http://localhost:8000/view/uuid",
  "expires_at": "2024-12-15T12:00:00",
  "has_password": false,
  "content_type": "text"
}
```

### Verify Password
```http
POST /api/secrets/{secret_id}/verify
Content-Type: application/json

Body:
{
  "password": "string"
}

Response:
{
  "verified": true
}
```

### Retrieve Secret (ONE-TIME VIEW)
```http
GET /api/secrets/{secret_id}?password=optional

Response:
{
  "content_type": "text",
  "content": "secret message",
  "file_name": null,
  "mime_type": null,
  "download_url": null
}
```

## 🔐 Security Features

- **HTTPS**: All data transmitted over HTTPS
- **Bcrypt**: Password hashing with bcrypt
- **Input Sanitization**: XSS and injection prevention
- **Rate Limiting**: 10 requests per minute per IP
- **File Validation**: MIME type checking and size limits
- **Secure Filenames**: Random UUID-based filenames
- **Auto-Deletion**: Immediate deletion after viewing

## 🎯 One-Time View Logic

The one-time view mechanism works as follows:

1. Secret is created and stored in database with `view_count = 0`
2. When accessed, the secret checks if `view_count >= 1` or `expiry_time` exceeded
3. If valid, content is returned and `view_count` is incremented
4. Secret is immediately deleted from database and file storage
5. Subsequent access attempts return 404 (redirects to expired page)

## 🧹 Automatic Cleanup

A background task runs every 5 minutes to:
- Find secrets that have expired (time-based)
- Delete associated files from storage
- Remove database entries
- Log cleanup operations

## 🌐 Deployment

### Production Deployment (Example with PostgreSQL)

1. **Set up PostgreSQL database**
```bash
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost/onetimeview
```

2. **Set production SECRET_KEY**
```bash
# Generate secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to .env
```

3. **Configure HTTPS**
```bash
# Use reverse proxy (nginx) or hosting platform
# Ensure all traffic uses HTTPS
```

4. **Run with production server**
```bash
gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Database Schema

### Secret Table
```sql
CREATE TABLE secrets (
    id VARCHAR(36) PRIMARY KEY,
    content_type VARCHAR(20) NOT NULL,
    content TEXT,
    file_path VARCHAR(255),
    file_name VARCHAR(255),
    mime_type VARCHAR(100),
    password_hash VARCHAR(100),
    expiry_time DATETIME,
    view_count INTEGER DEFAULT 0,
    max_views INTEGER DEFAULT 1,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🎨 SEO Keywords

The application is optimized for:
- one time message
- self destruct message
- secure file sharing
- burn after reading
- one time link generator
- ephemeral messaging
- private message sharing

## 💰 Monetization

### Free Tier
- Text secrets only
- 24-hour expiration
- No password protection
- Ads placeholder

### Premium Tier ($9/month)
- Image, video, file uploads (500MB)
- Password protection
- Custom expiry times
- Ad-free experience

## 🧪 Testing

Test the application:

```bash
# Start the server
python -m uvicorn backend.main:app --reload

# Test in browser
# 1. Create a text secret at http://localhost:8000/create
# 2. Copy the generated link
# 3. Open link - you should see the warning
# 4. View the secret - content should display
# 5. Try opening link again - should redirect to /expired
```

## 📝 License

This project is provided as-is for educational and commercial use.

## 🤝 Support

For questions or issues:
- Email: support@onetimeview.com
- Documentation: See this README

## 🔄 Future Enhancements

Potential improvements:
- Payment integration (Stripe)
- Cloud storage (AWS S3, Google Cloud Storage)
- Analytics dashboard
- API keys for programmatic access
- Self-destruct countdown timer
- Notification when secret is viewed
