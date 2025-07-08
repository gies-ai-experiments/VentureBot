"""
Streaming Configuration Module for Chainlit VentureBot
Provides centralized configuration for streaming behavior
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

class StreamingMode(Enum):
    """Available streaming modes"""
    DISABLED = "disabled"
    BASIC = "basic"
    ADVANCED = "advanced"
    FULL = "full"

class StreamingSpeed(Enum):
    """Predefined streaming speeds"""
    SLOW = 0.05
    NORMAL = 0.02
    FAST = 0.01
    INSTANT = 0.001

@dataclass
class StreamingConfig:
    """Main streaming configuration"""
    
    # Basic streaming settings
    enabled: bool = True
    mode: StreamingMode = StreamingMode.ADVANCED
    speed: StreamingSpeed = StreamingSpeed.NORMAL
    
    # Token streaming settings
    token_delay: float = 0.02
    chunk_size: int = 1
    buffer_size: int = 1024
    
    # Connection settings
    max_retries: int = 3
    timeout: int = 30
    connection_retry_delay: float = 1.0
    
    # UI/UX settings
    show_thinking: bool = True
    thinking_message: str = "🤔 Thinking..."
    typing_indicator: bool = True
    progress_indicators: bool = True
    
    # Chain of thought settings
    enable_cot: bool = True
    cot_mode: str = "full"  # "hidden", "tool_call", "full"
    show_step_progress: bool = True
    
    # Performance settings
    batch_tokens: bool = False
    batch_size: int = 5
    rate_limit: bool = True
    max_tokens_per_second: int = 100
    
    # Debug settings
    debug_mode: bool = False
    log_tokens: bool = False
    log_timing: bool = False
    
    # Advanced features
    simulate_typing: bool = False
    typing_wpm: int = 60
    typing_variance: float = 0.2
    
    # Error handling
    graceful_fallback: bool = True
    error_recovery: bool = True
    max_error_retries: int = 2

@dataclass
class VentureBotStreamingConfig:
    """VentureBot specific streaming configuration"""
    
    # Agent-specific settings
    onboarding_speed: StreamingSpeed = StreamingSpeed.NORMAL
    idea_generation_speed: StreamingSpeed = StreamingSpeed.FAST
    validation_speed: StreamingSpeed = StreamingSpeed.NORMAL
    
    # Message type specific settings
    welcome_message_streaming: bool = True
    error_message_streaming: bool = True
    system_message_streaming: bool = False
    
    # Tool streaming settings
    tool_call_streaming: bool = True
    tool_response_streaming: bool = True
    web_search_streaming: bool = True
    
    # Multi-agent settings
    agent_handoff_indicator: bool = True
    agent_thinking_messages: Dict[str, str] = field(default_factory=lambda: {
        "onboarding": "🎯 Getting to know you...",
        "idea_generator": "💡 Generating ideas...",
        "validator": "✅ Validating concept...",
        "product_manager": "📋 Planning product...",
        "prompt_engineer": "🔧 Crafting prompts..."
    })

class StreamingConfigManager:
    """Manages streaming configuration from environment and settings"""
    
    def __init__(self):
        self.base_config = StreamingConfig()
        self.venture_config = VentureBotStreamingConfig()
        
    def load_from_env(self) -> StreamingConfig:
        """Load configuration from environment variables"""
        config = StreamingConfig()
        
        # Basic settings
        config.enabled = os.getenv("STREAMING_ENABLED", "true").lower() == "true"
        config.mode = StreamingMode(os.getenv("STREAMING_MODE", "advanced"))
        
        # Speed settings
        speed_value = os.getenv("STREAMING_SPEED", "normal")
        if speed_value in ["slow", "normal", "fast", "instant"]:
            config.speed = StreamingSpeed[speed_value.upper()]
        else:
            config.token_delay = float(speed_value)
            
        # Performance settings
        config.batch_tokens = os.getenv("STREAMING_BATCH_TOKENS", "false").lower() == "true"
        config.batch_size = int(os.getenv("STREAMING_BATCH_SIZE", "5"))
        
        # Debug settings
        config.debug_mode = os.getenv("STREAMING_DEBUG", "false").lower() == "true"
        config.log_tokens = os.getenv("STREAMING_LOG_TOKENS", "false").lower() == "true"
        
        return config
        
    def load_from_dict(self, config_dict: Dict[str, Any]) -> StreamingConfig:
        """Load configuration from dictionary"""
        config = StreamingConfig()
        
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
                
        return config
        
    def get_config_for_agent(self, agent_name: str) -> StreamingConfig:
        """Get optimized config for specific agent"""
        config = self.base_config
        
        # Agent-specific optimizations
        if agent_name == "onboarding":
            config.speed = self.venture_config.onboarding_speed
            config.show_thinking = True
            config.thinking_message = self.venture_config.agent_thinking_messages.get(agent_name, "🤔 Thinking...")
            
        elif agent_name == "idea_generator":
            config.speed = self.venture_config.idea_generation_speed
            config.simulate_typing = True
            config.enable_cot = True
            
        elif agent_name == "validator":
            config.speed = self.venture_config.validation_speed
            config.show_step_progress = True
            config.enable_cot = True
            
        return config
        
    def get_production_config(self) -> StreamingConfig:
        """Get optimized configuration for production"""
        config = StreamingConfig()
        
        # Production optimizations
        config.mode = StreamingMode.BASIC
        config.speed = StreamingSpeed.FAST
        config.debug_mode = False
        config.log_tokens = False
        config.log_timing = False
        config.simulate_typing = False
        config.show_thinking = True
        config.graceful_fallback = True
        config.error_recovery = True
        
        return config
        
    def get_development_config(self) -> StreamingConfig:
        """Get configuration optimized for development"""
        config = StreamingConfig()
        
        # Development optimizations
        config.mode = StreamingMode.FULL
        config.speed = StreamingSpeed.NORMAL
        config.debug_mode = True
        config.log_tokens = True
        config.log_timing = True
        config.simulate_typing = True
        config.show_thinking = True
        config.enable_cot = True
        config.cot_mode = "full"
        
        return config

# Predefined configurations
STREAMING_CONFIGS = {
    "minimal": StreamingConfig(
        enabled=True,
        mode=StreamingMode.BASIC,
        speed=StreamingSpeed.FAST,
        show_thinking=False,
        enable_cot=False,
        debug_mode=False
    ),
    
    "standard": StreamingConfig(
        enabled=True,
        mode=StreamingMode.ADVANCED,
        speed=StreamingSpeed.NORMAL,
        show_thinking=True,
        enable_cot=True,
        simulate_typing=False
    ),
    
    "enhanced": StreamingConfig(
        enabled=True,
        mode=StreamingMode.FULL,
        speed=StreamingSpeed.NORMAL,
        show_thinking=True,
        enable_cot=True,
        simulate_typing=True,
        show_step_progress=True,
        progress_indicators=True
    ),
    
    "demo": StreamingConfig(
        enabled=True,
        mode=StreamingMode.FULL,
        speed=StreamingSpeed.SLOW,
        show_thinking=True,
        enable_cot=True,
        simulate_typing=True,
        typing_wpm=40,
        show_step_progress=True,
        progress_indicators=True
    )
}

def get_config(config_name: str = "standard") -> StreamingConfig:
    """Get a predefined configuration by name"""
    return STREAMING_CONFIGS.get(config_name, STREAMING_CONFIGS["standard"])

def create_custom_config(**kwargs) -> StreamingConfig:
    """Create a custom configuration with overrides"""
    config = StreamingConfig()
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
            
    return config

# Environment-based configuration loading
def load_config_from_environment() -> StreamingConfig:
    """Load configuration from environment variables"""
    manager = StreamingConfigManager()
    return manager.load_from_env()

# Example usage and testing
if __name__ == "__main__":
    # Test configuration loading
    print("Testing streaming configuration...")
    
    # Load different configs
    configs = ["minimal", "standard", "enhanced", "demo"]
    
    for config_name in configs:
        config = get_config(config_name)
        print(f"\n{config_name.upper()} Config:")
        print(f"  Mode: {config.mode.value}")
        print(f"  Speed: {config.speed.value}")
        print(f"  CoT Enabled: {config.enable_cot}")
        print(f"  Simulate Typing: {config.simulate_typing}")
        
    # Test custom config
    custom = create_custom_config(
        speed=StreamingSpeed.FAST,
        simulate_typing=True,
        typing_wpm=80,
        debug_mode=True
    )
    print(f"\nCUSTOM Config:")
    print(f"  Speed: {custom.speed.value}")
    print(f"  Typing WPM: {custom.typing_wpm}")
    print(f"  Debug Mode: {custom.debug_mode}")