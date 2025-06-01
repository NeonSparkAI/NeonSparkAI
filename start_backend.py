
#!/usr/bin/env python3
"""
NeonSpark AI Backend Startup Script
Handles backend initialization, dependency checking, and server startup
"""

import sys
import os
import subprocess
import platform
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for startup script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    logger = logging.getLogger(__name__)
    
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    logger.info(f"Python version: {platform.python_version()} ✓")
    return True

def check_and_install_tesseract():
    """Check if Tesseract OCR is installed"""
    logger = logging.getLogger(__name__)
    
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, check=True)
        logger.info("Tesseract OCR found ✓")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Tesseract OCR not found")
        logger.info("Please install Tesseract OCR:")
        
        if platform.system() == "Windows":
            logger.info("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        elif platform.system() == "Darwin":  # macOS
            logger.info("Run: brew install tesseract")
        else:  # Linux
            logger.info("Run: sudo apt-get install tesseract-ocr")
        
        return False

def install_dependencies():
    """Install Python dependencies"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Installing Python dependencies...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, capture_output=True, text=True)
        
        logger.info("Dependencies installed successfully ✓")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def check_environment():
    """Check environment variables"""
    logger = logging.getLogger(__name__)
    
    env_file = Path('.env')
    if not env_file.exists():
        logger.error(".env file not found")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        logger.error("GEMINI_API_KEY not found in .env file")
        return False
    
    logger.info("Environment configuration ✓")
    return True

def start_server():
    """Start the FastAPI server"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting NeonSpark AI Backend server...")
        logger.info("Server will be available at: http://localhost:3000")
        logger.info("API documentation: http://localhost:3000/api/docs")
        logger.info("Press Ctrl+C to stop the server")
        
        # Import and run the application
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=3000,
            reload=False,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("NeonSpark AI Backend - Starting Up")
    logger.info("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # System checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_and_install_tesseract():
        logger.warning("Tesseract OCR not available - OCR features will be limited")
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Start server
    if not start_server():
        sys.exit(1)

if __name__ == "__main__":
    main()
