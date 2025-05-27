import os
import yaml
from dotenv import load_dotenv
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml file."""
    config_path = os.path.join("agentlab_v4_claude", "config.yaml")
    return yaml.safe_load(open(config_path))

def load_env() -> None:
    """Load environment variables from .env file."""
    dotenv_path = os.path.join(os.getcwd(), ".env")
    load_dotenv(dotenv_path)

def get_anthropic_api_key() -> str:
    """Get Anthropic API key from environment variables."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    return api_key 