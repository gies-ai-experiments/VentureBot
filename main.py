# main.py
import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# The AGENT_DIR will be the root of your project, where main.py is located.
# get_fast_api_app will scan this directory for agent modules (manager/, etc.)
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration for the ADK FastAPI app

# Replace hard-wired SQLite URL with env-driven value
SESSION_DB_URL = os.getenv("DATABASE_URL")  # falls back to .env

# (OPTIONAL) engine args for Postgres pooling, keep as-is if ADK manages engine
ALLOWED_ORIGINS = ["*"]  # Allow all origins for simplicity, adjust if needed for security
SERVE_WEB_INTERFACE = True # This ensures the ADK Web UI is served

# Get the FastAPI application instance from ADK
app: FastAPI = get_fast_api_app(
    agent_dir=AGENT_DIR,
    session_db_url=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# You can add custom FastAPI routes here if needed in the future
# @app.get("/custom-hello")
# async def read_custom_hello():
#     return {"message": "Hello from custom route"}

if __name__ == "__main__":
    # This block is for running locally, e.g., python main.py
    # The Dockerfile CMD will run uvicorn directly.
    # The PORT environment variable is used here for consistency with container environments.
    port = int(os.environ.get("PORT", 80)) # Default to port 80
    uvicorn.run(app, host="0.0.0.0", port=port) 