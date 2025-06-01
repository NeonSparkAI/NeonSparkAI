# This makes the api_routes directory a Python package
# All your route modules will be imported here

from .ai_router import router as ai_router

__all__ = ['ai_router']
