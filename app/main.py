"""Primary ASGI entrypoint for the application tier."""

from __future__ import annotations

from .vinayak.interface.api.main import app 
from dotenv import load_dotenv
load_dotenv()
__all__ = ["app"]
