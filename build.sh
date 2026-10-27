#!/usr/bin/env bash
# Build script for Render
set -e  # Exit immediately if any command fails

echo "🔧 Installing Python dependencies..."
# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "📁 Creating necessary directories..."
# Create necessary directories
mkdir -p uploads
touch uploads/.gitkeep

echo "🔄 Running database migrations..."
python migrate.py || echo "⚠️ Migration script completed with warnings or DB unreachable during build"

echo "✅ Build completed successfully!"
