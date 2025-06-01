from setuptools import setup, find_packages

setup(
    name="neonspark-ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core
        'fastapi==0.115.12',
        'uvicorn[standard]==0.34.3',
        'python-multipart==0.0.20',
        'websockets==15.0.1',
        'pydantic==2.11.5',
        'pydantic-settings==2.7.1',
        
        # AI/ML
        'google-generativeai==0.8.5',
        'google-ai-generativelanguage==0.6.15',
        'opencv-python-headless==4.11.0.86',
        'Pillow==11.2.1',
        'pytesseract==0.3.13',
        'numpy==2.2.6',
        
        # Async
        'aiofiles==24.1.0',
        'aiohttp==3.9.5',
        'anyio==4.9.0',
        
        # HTTP/API
        'requests==2.32.3',
        'httpx==0.27.0',
        
        # Utils
        'psutil==7.0.0',
        'python-dotenv==1.1.0',
        'python-magic==0.4.27',
        'python-jose[cryptography]==3.5.0',
        'passlib[bcrypt]==1.7.4',
        'structlog==25.3.0',
        'fastapi-cors==0.0.6',
        
        # Google API
        'google-api-python-client==2.170.0',
        'google-auth==2.40.2',
        'google-auth-httplib2==0.2.0',
        'google-auth-oauthlib==1.2.0',
        'google-api-core==2.24.2',
        'googleapis-common-protos==1.70.0',
        
        # Security
        'cryptography==45.0.3',
        'pyjwt==2.10.1',
    ],
    python_requires='>=3.11',
)
