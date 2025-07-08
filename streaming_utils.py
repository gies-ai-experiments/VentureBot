"""
Streaming Utilities for Chainlit VentureBot
Helper functions and utilities for streaming operations
"""

import asyncio
import json
import time
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamingMetrics:
    """Metrics for streaming performance analysis"""
    start_time: float
    end_time: Optional[float] = None
    total_tokens: int = 0
    total_characters: int = 0
    chunks_processed: int = 0
    errors: int = 0
    average_latency: float = 0.0
    tokens_per_second: float = 0.0
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        if self.end_time:
            duration = self.end_time - self.start_time
            self.tokens_per_second = self.total_tokens / duration if duration > 0 else 0
            self.average_latency = duration / self.chunks_processed if self.chunks_processed > 0 else 0

class StreamingUtils:
    """Utility functions for streaming operations"""
    
    @staticmethod
    async def text_to_tokens(text: str, 
                           chunk_size: int = 1,
                           delay: float = 0.01) -> AsyncGenerator[str, None]:
        """Convert text to streaming tokens with configurable chunking"""
        for i in range(0, len(text), chunk_size):
            token = text[i:i + chunk_size]
            yield token
            if delay > 0:
                await asyncio.sleep(delay)
                
    @staticmethod
    async def word_based_streaming(text: str, 
                                 delay: float = 0.1) -> AsyncGenerator[str, None]:
        """Stream text word by word instead of character by character"""
        words = text.split()
        for i, word in enumerate(words):
            # Add space before word (except first word)
            token = f" {word}" if i > 0 else word
            yield token
            if delay > 0:
                await asyncio.sleep(delay)
                
    @staticmethod
    async def sentence_based_streaming(text: str, 
                                     delay: float = 0.5) -> AsyncGenerator[str, None]:
        """Stream text sentence by sentence"""
        # Split by sentence endings
        sentences = re.split(r'([.!?]+)', text)
        current_sentence = ""
        
        for part in sentences:
            current_sentence += part
            if re.match(r'[.!?]+', part):
                yield current_sentence
                current_sentence = ""
                if delay > 0:
                    await asyncio.sleep(delay)
                    
        # Yield remaining text
        if current_sentence.strip():
            yield current_sentence
            
    @staticmethod
    async def simulate_typing(text: str, 
                            wpm: int = 60,
                            variance: float = 0.2,
                            pause_on_punctuation: bool = True) -> AsyncGenerator[str, None]:
        """Simulate human typing with realistic delays"""
        import random
        
        # Calculate base delay (WPM to characters per second)
        chars_per_second = wpm * 5 / 60  # ~5 chars per word
        base_delay = 1.0 / chars_per_second
        
        for char in text:
            yield char
            
            # Base delay with variance
            delay = base_delay * (1 + random.uniform(-variance, variance))
            
            # Longer pauses for punctuation
            if pause_on_punctuation and char in '.!?':
                delay *= 3
            elif char in ',;:':
                delay *= 2
                
            await asyncio.sleep(delay)
            
    @staticmethod
    async def batch_tokens(token_generator: AsyncGenerator[str, None], 
                         batch_size: int = 5) -> AsyncGenerator[str, None]:
        """Batch tokens for more efficient streaming"""
        batch = []
        
        async for token in token_generator:
            batch.append(token)
            
            if len(batch) >= batch_size:
                yield ''.join(batch)
                batch = []
                
        # Yield remaining tokens
        if batch:
            yield ''.join(batch)
            
    @staticmethod
    async def rate_limited_streaming(token_generator: AsyncGenerator[str, None],
                                   max_tokens_per_second: int = 100) -> AsyncGenerator[str, None]:
        """Apply rate limiting to token streaming"""
        min_delay = 1.0 / max_tokens_per_second
        last_token_time = 0
        
        async for token in token_generator:
            current_time = time.time()
            time_since_last = current_time - last_token_time
            
            if time_since_last < min_delay:
                await asyncio.sleep(min_delay - time_since_last)
                
            yield token
            last_token_time = time.time()
            
    @staticmethod
    def create_progress_bar(current: int, total: int, width: int = 20) -> str:
        """Create a progress bar for streaming operations"""
        if total == 0:
            return "⏳ Processing..."
            
        percentage = (current / total) * 100
        filled = int((current / total) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"⏳ {bar} {percentage:.1f}%"
        
    @staticmethod
    def format_streaming_metrics(metrics: StreamingMetrics) -> str:
        """Format streaming metrics for display"""
        if not metrics.end_time:
            return "⏳ Streaming in progress..."
            
        metrics.calculate_metrics()
        
        return f"""📊 **Streaming Metrics**
• Duration: {metrics.end_time - metrics.start_time:.2f}s
• Total Tokens: {metrics.total_tokens}
• Characters: {metrics.total_characters}
• Speed: {metrics.tokens_per_second:.1f} tokens/sec
• Latency: {metrics.average_latency:.3f}s avg
• Errors: {metrics.errors}"""

class StreamingDebugger:
    """Debug utilities for streaming operations"""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.logs = []
        
    def log_token(self, token: str, timestamp: float = None):
        """Log a streaming token"""
        if not self.enabled:
            return
            
        log_entry = {
            "timestamp": timestamp or time.time(),
            "token": token,
            "length": len(token),
            "type": "token"
        }
        self.logs.append(log_entry)
        
    def log_event(self, event: str, data: Any = None):
        """Log a streaming event"""
        if not self.enabled:
            return
            
        log_entry = {
            "timestamp": time.time(),
            "event": event,
            "data": data,
            "type": "event"
        }
        self.logs.append(log_entry)
        
    def get_debug_summary(self) -> Dict[str, Any]:
        """Get debug summary"""
        if not self.logs:
            return {"message": "No debug data available"}
            
        token_logs = [log for log in self.logs if log["type"] == "token"]
        event_logs = [log for log in self.logs if log["type"] == "event"]
        
        total_chars = sum(log["length"] for log in token_logs)
        start_time = min(log["timestamp"] for log in self.logs)
        end_time = max(log["timestamp"] for log in self.logs)
        duration = end_time - start_time
        
        return {
            "total_tokens": len(token_logs),
            "total_characters": total_chars,
            "total_events": len(event_logs),
            "duration": duration,
            "characters_per_second": total_chars / duration if duration > 0 else 0,
            "events": [log["event"] for log in event_logs],
            "first_token_time": token_logs[0]["timestamp"] if token_logs else None,
            "last_token_time": token_logs[-1]["timestamp"] if token_logs else None
        }

class StreamingValidator:
    """Validation utilities for streaming content"""
    
    @staticmethod
    def validate_streaming_content(content: str) -> Dict[str, Any]:
        """Validate streaming content for quality and safety"""
        issues = []
        
        # Check for empty content
        if not content.strip():
            issues.append("Empty content")
            
        # Check for malformed JSON
        if content.strip().startswith('{') or content.strip().startswith('['):
            try:
                json.loads(content)
            except json.JSONDecodeError:
                issues.append("Malformed JSON content")
                
        # Check for potential security issues
        suspicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'onload=',
            r'eval\(',
            r'exec\('
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Suspicious pattern detected: {pattern}")
                
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "character_count": len(content),
            "word_count": len(content.split()),
            "line_count": content.count('\n') + 1
        }
        
    @staticmethod
    def sanitize_streaming_content(content: str) -> str:
        """Sanitize content for safe streaming and convert HTML to markdown"""
        # Remove potential script tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove javascript: links
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        
        # Remove onload and similar attributes
        content = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
        
        # Convert HTML formatting to markdown
        content = re.sub(r'<u>(.*?)</u>', r'**\1**', content, flags=re.IGNORECASE)  # underline to bold
        content = re.sub(r'<b>(.*?)</b>', r'**\1**', content, flags=re.IGNORECASE)  # bold to bold
        content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content, flags=re.IGNORECASE)  # strong to bold
        content = re.sub(r'<em>(.*?)</em>', r'*\1*', content, flags=re.IGNORECASE)  # em to italic
        content = re.sub(r'<i>(.*?)</i>', r'*\1*', content, flags=re.IGNORECASE)  # italic to italic
        
        return content

class StreamingCache:
    """Simple caching for streaming operations"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        
    def get(self, key: str) -> Optional[str]:
        """Get cached streaming result"""
        return self.cache.get(key)
        
    def set(self, key: str, value: str):
        """Cache streaming result"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            
        self.cache[key] = value
        
    def clear(self):
        """Clear cache"""
        self.cache.clear()

# Example usage and testing functions
async def demo_streaming_utils():
    """Demonstrate streaming utilities"""
    print("🔧 Streaming Utils Demo")
    print("=" * 50)
    
    text = "Hello! This is a demonstration of streaming utilities. Let's see how they work."
    
    # Character-based streaming
    print("\n📝 Character-based streaming:")
    async for token in StreamingUtils.text_to_tokens(text, chunk_size=1, delay=0.05):
        print(token, end='', flush=True)
        
    print("\n\n🔤 Word-based streaming:")
    async for token in StreamingUtils.word_based_streaming(text, delay=0.2):
        print(token, end='', flush=True)
        
    print("\n\n📖 Sentence-based streaming:")
    async for token in StreamingUtils.sentence_based_streaming(text, delay=0.5):
        print(f"[{token}]", end=' ', flush=True)
        
    print("\n\n⌨️ Typing simulation:")
    async for token in StreamingUtils.simulate_typing(text, wpm=120, variance=0.3):
        print(token, end='', flush=True)
        
    print("\n\n✅ Demo completed!")

async def test_streaming_performance():
    """Test streaming performance"""
    print("\n🚀 Performance Test")
    print("=" * 50)
    
    text = "This is a performance test. " * 100  # Repeat for larger text
    
    # Test different streaming methods
    methods = [
        ("Character streaming", StreamingUtils.text_to_tokens(text, chunk_size=1, delay=0.001)),
        ("Word streaming", StreamingUtils.word_based_streaming(text, delay=0.01)),
        ("Batch streaming", StreamingUtils.batch_tokens(
            StreamingUtils.text_to_tokens(text, chunk_size=1, delay=0.001), 
            batch_size=10
        ))
    ]
    
    for method_name, generator in methods:
        start_time = time.time()
        token_count = 0
        
        async for token in generator:
            token_count += 1
            
        duration = time.time() - start_time
        print(f"{method_name}: {token_count} tokens in {duration:.3f}s ({token_count/duration:.1f} tokens/sec)")

if __name__ == "__main__":
    # Run demos
    asyncio.run(demo_streaming_utils())
    asyncio.run(test_streaming_performance())