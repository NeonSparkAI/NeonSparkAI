#!/bin/bash
set -e  # Exit on error

# Set up logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Install system dependencies
log "Updating package lists..."
apt-get update -qq

# Install Tesseract OCR with English language support
log "Installing Tesseract OCR..."
apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
log "Verifying Tesseract installation..."
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version | head -n 1)
    log "Tesseract installed: $TESSERACT_VERSION"
    
    # Check if Tesseract data directory exists
    if [ -d "/usr/share/tesseract-ocr/4.00/tessdata" ]; then
        export TESSDATA_PREFIX="/usr/share/tesseract-ocr"
        log "Set TESSDATA_PREFIX to $TESSDATA_PREFIX"
    fi
    
    # Verify Tesseract can be executed
    tesseract --list-langs || log "Warning: Tesseract language list command failed"
else
    log "Error: Tesseract installation failed!"
    exit 1
fi

# Install Python dependencies
log "Installing Python dependencies..."
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt

log "Build completed successfully!"
