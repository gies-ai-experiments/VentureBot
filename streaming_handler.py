import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import chainlit as cl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamingState(Enum):
    """States for streaming process"""
    IDLE = "idle"
    CONNECTING = "connecting"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class StreamingConfig:
    """Configuration for streaming behavior"""
    token_delay: float = 0.01  # Delay between tokens in seconds
    chunk_size: int = 1  # Number of characters per chunk
    max_retries: int = 3  # Maximum retry attempts
    timeout: int = 30  # Request timeout in seconds
    buffer_size: int = 1024  # Internal buffer size
    show_thinking: bool = True  # Show thinking indicators
    enable_cot: bool = True  # Enable chain of thought streaming

class StreamingHandler:
    """Advanced streaming handler for Chainlit integration"""
    
    def __init__(self, config: StreamingConfig = None):
        self.config = config or StreamingConfig()
        self.state = StreamingState.IDLE
        self.current_message: Optional[cl.Message] = None
        self.stream_buffer = ""
        self.token_count = 0
        self.error_count = 0
        
    async def create_streaming_message(self, author: str = "VentureBot") -> cl.Message:
        """Create a new streaming message"""
        self.current_message = cl.Message(content="", author=author)
        self.state = StreamingState.CONNECTING
        return self.current_message
        
    async def stream_response(self, 
                            token_generator: AsyncGenerator[str, None],
                            message: cl.Message = None) -> bool:
        """Stream a response using the token generator"""
        if message:
            self.current_message = message
            
        if not self.current_message:
            logger.error("No message available for streaming")
            return False
            
        self.state = StreamingState.STREAMING
        self.token_count = 0
        
        try:
            async for token in token_generator:
                await self._stream_token(token)
                
            await self.current_message.send()
            self.state = StreamingState.COMPLETED
            logger.info(f"Streaming completed. Total tokens: {self.token_count}")
            return True
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            self.state = StreamingState.ERROR
            await self._handle_streaming_error(str(e))
            return False
            
    async def _stream_token(self, token: str):
        """Stream a single token with rate limiting"""
        if not token:
            return
            
        # Apply chunking if needed
        if self.config.chunk_size > 1:
            self.stream_buffer += token
            if len(self.stream_buffer) >= self.config.chunk_size:
                await self.current_message.stream_token(self.stream_buffer)
                self.stream_buffer = ""
        else:
            await self.current_message.stream_token(token)
            
        self.token_count += len(token)
        
        # Rate limiting
        if self.config.token_delay > 0:
            await asyncio.sleep(self.config.token_delay)
            
    async def _handle_streaming_error(self, error_message: str):
        """Handle streaming errors gracefully"""
        error_token = f"\n\n❌ **Streaming Error**: {error_message}"
        await self.current_message.stream_token(error_token)
        await self.current_message.send()
        
    async def stream_with_thinking(self, 
                                 token_generator: AsyncGenerator[str, None],
                                 thinking_message: str = "🤔 Thinking...") -> bool:
        """Stream response with thinking indicator"""
        if not self.config.show_thinking:
            return await self.stream_response(token_generator)
            
        # Show thinking indicator
        if self.current_message:
            await self.current_message.stream_token(thinking_message)
            await asyncio.sleep(0.5)  # Brief pause
            
            # Clear thinking message and start actual response
            self.current_message.content = ""
            
        return await self.stream_response(token_generator)

class ChainOfThoughtStreamer:
    """Specialized streamer for chain of thought steps"""
    
    def __init__(self, config: StreamingConfig = None):
        self.config = config or StreamingConfig()
        self.steps: List[cl.Step] = []
        self.current_step: Optional[cl.Step] = None
        
    async def create_step(self, name: str, type: str = "tool") -> cl.Step:
        """Create a new chain of thought step"""
        step = cl.Step(name=name, type=type)
        self.steps.append(step)
        self.current_step = step
        return step
        
    async def stream_step_output(self, 
                               step: cl.Step,
                               token_generator: AsyncGenerator[str, None]) -> bool:
        """Stream output for a specific step"""
        try:
            step_content = ""
            async for token in token_generator:
                step_content += token
                step.output = step_content
                await step.update()
                
                # Rate limiting
                if self.config.token_delay > 0:
                    await asyncio.sleep(self.config.token_delay)
                    
            await step.send()
            return True
            
        except Exception as e:
            logger.error(f"Step streaming error: {str(e)}")
            step.output = f"❌ Error: {str(e)}"
            await step.update()
            return False
            
    async def stream_multiple_steps(self, 
                                  steps_data: List[Dict[str, Any]]) -> bool:
        """Stream multiple chain of thought steps"""
        try:
            for step_data in steps_data:
                step = await self.create_step(
                    name=step_data.get("name", "Step"),
                    type=step_data.get("type", "tool")
                )
                
                if "token_generator" in step_data:
                    await self.stream_step_output(step, step_data["token_generator"])
                elif "content" in step_data:
                    # Stream static content
                    async def static_generator():
                        for char in step_data["content"]:
                            yield char
                    await self.stream_step_output(step, static_generator())
                    
            return True
            
        except Exception as e:
            logger.error(f"Multiple steps streaming error: {str(e)}")
            return False

class StreamingUtils:
    """Utility functions for streaming operations"""
    
    @staticmethod
    async def text_to_tokens(text: str, chunk_size: int = 1) -> AsyncGenerator[str, None]:
        """Convert text to streaming tokens"""
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]
            
    @staticmethod
    async def simulate_typing(text: str, 
                            wpm: int = 60,
                            variance: float = 0.2) -> AsyncGenerator[str, None]:
        """Simulate human typing speed"""
        import random
        
        # Calculate base delay (60 WPM = 1 word per second, ~5 chars per word)
        base_delay = 1.0 / (wpm * 5 / 60)
        
        for char in text:
            yield char
            
            # Add variance to make it feel more human
            delay = base_delay * (1 + random.uniform(-variance, variance))
            await asyncio.sleep(delay)
            
    @staticmethod
    async def batch_tokens(token_generator: AsyncGenerator[str, None], 
                         batch_size: int = 5) -> AsyncGenerator[str, None]:
        """Batch tokens for more efficient streaming"""
        batch = ""
        count = 0
        
        async for token in token_generator:
            batch += token
            count += 1
            
            if count >= batch_size:
                yield batch
                batch = ""
                count = 0
                
        # Yield remaining tokens
        if batch:
            yield batch
            
    @staticmethod
    def create_progress_indicator(current: int, total: int) -> str:
        """Create a progress indicator for streaming"""
        if total == 0:
            return "⏳ Processing..."
            
        percentage = (current / total) * 100
        filled = int(percentage // 5)  # 20 blocks for 100%
        bar = "█" * filled + "░" * (20 - filled)
        return f"⏳ Progress: {bar} {percentage:.1f}%"

# Factory function for easy handler creation
def create_streaming_handler(config: Dict[str, Any] = None) -> StreamingHandler:
    """Factory function to create a streaming handler with config"""
    stream_config = StreamingConfig()
    
    if config:
        for key, value in config.items():
            if hasattr(stream_config, key):
                setattr(stream_config, key, value)
                
    return StreamingHandler(stream_config)

# Example usage functions
async def example_basic_streaming():
    """Example of basic streaming usage"""
    handler = create_streaming_handler()
    message = await handler.create_streaming_message()
    
    async def sample_generator():
        text = "Hello, this is a streaming response!"
        async for char in StreamingUtils.text_to_tokens(text):
            yield char
            
    await handler.stream_response(sample_generator(), message)
    
async def example_cot_streaming():
    """Example of chain of thought streaming"""
    cot_streamer = ChainOfThoughtStreamer()
    
    steps_data = [
        {"name": "Analysis", "content": "Analyzing your request..."},
        {"name": "Planning", "content": "Creating a plan..."},
        {"name": "Execution", "content": "Executing the plan..."}
    ]
    
    await cot_streamer.stream_multiple_steps(steps_data)