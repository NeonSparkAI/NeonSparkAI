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
log "Installing Tesseract OCR and dependencies..."
apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    liblept5 \
    libtesseract5 \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
log "Verifying Tesseract installation..."
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version | head -n 1)
    log "Tesseract installed: $TESSERACT_VERSION"
    
    # Set TESSDATA_PREFIX to the correct location
    TESSDATA_PATH="/usr/share/tesseract-ocr/4.00/tessdata"
    if [ ! -d "$TESSDATA_PATH" ]; then
        TESSDATA_PATH="/usr/share/tesseract-ocr/tessdata"
        if [ ! -d "$TESSDATA_PATH" ]; then
            TESSDATA_PATH="/usr/share/tesseract/tessdata"
        fi
    fi
    
    if [ -d "$TESSDATA_PATH" ]; then
        export TESSDATA_PREFIX=$(dirname "$(dirname "$TESSDATA_PATH")")
        echo "TESSDATA_PREFIX=$TESSDATA_PREFIX" >> /etc/environment
        log "Set TESSDATA_PREFIX to $TESSDATA_PREFIX"
    else
        log "Warning: Could not find Tesseract data directory"
    fi
    
    # Verify Tesseract can be executed and list languages
    log "Available Tesseract languages:"
    tesseract --list-langs || log "Warning: Failed to list Tesseract languages"
else
    log "Error: Tesseract installation failed!"
    exit 1
fi

# Install Python package in development mode
log "Installing Python package in development mode..."
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -e .

log "Build completed successfully!"
