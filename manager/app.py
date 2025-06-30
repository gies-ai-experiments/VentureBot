import os
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from .agent import root_agent

# Configuration for the ADK FastAPI app
SESSION_DB_URL = "sqlite:///./sessions.db"  # Default SQLite DB in the current directory
ALLOWED_ORIGINS = ["*"]  # Allow all origins for simplicity
SERVE_WEB_INTERFACE = True  # This ensures the ADK Web UI is served

# Get the FastAPI application instance from ADK
app: FastAPI = get_fast_api_app(
    agent_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Point to VentureBots directory
    session_db_url=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
) 