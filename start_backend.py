
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
        # First check if Tesseract is in PATH
        result = subprocess.run(['which', 'tesseract'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            # If not in PATH, check common locations
            common_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract'  # For macOS
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    os.environ['PATH'] = f"{os.path.dirname(path)}:{os.environ.get('PATH', '')}"
                    break
        
        # Now check version
        version_result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True, 
            text=True, 
            check=True
        )
        
        logger.info(f"Tesseract found: {version_result.stdout.split('\n')[0]}")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Tesseract OCR not found or not accessible: {str(e)}")
        logger.warning("OCR features will be limited")
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
        # Get port from environment variable or use default
        port = int(os.getenv('PORT', '3000'))
        host = os.getenv('HOST', '0.0.0.0')
        
        logger.info("=" * 60)
        logger.info(f"Starting NeonSpark AI Backend server on {host}:{port}")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info("=" * 60)
        
        # Log important environment variables (without sensitive values)
        env_vars = ['HOST', 'PORT', 'ENVIRONMENT', 'LOG_LEVEL']
        logger.info("Environment variables:")
        for var in env_vars:
            if os.getenv(var):
                logger.info(f"  {var}: {os.getenv(var)}")
        
        # Import and run the application
        import uvicorn
        
        # Configure uvicorn
        config = uvicorn.Config(
            app="main:app",
            host=host,
            port=port,
            log_level=os.getenv('LOG_LEVEL', 'info').lower(),
            access_log=True,
            workers=int(os.getenv('WEB_CONCURRENCY', '1')),
            timeout_keep_alive=300,  # 5 minutes
            proxy_headers=True,
            forwarded_allow_ips='*'  # For handling X-Forwarded-* headers
        )
        
        server = uvicorn.Server(config)
        server.run()
        
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
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
