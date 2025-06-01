#!/bin/bash
set -e  # Exit on error

# Install system dependencies
echo "Updating package lists..."
apt-get update

echo "Installing Tesseract OCR with English language pack..."
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Verify Tesseract installation
echo "Verifying Tesseract installation..."
tesseract --version || echo "Tesseract installation failed!"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "Build completed successfully!"
