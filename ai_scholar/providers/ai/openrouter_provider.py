import time
import requests
from typing import Optional, Dict, Any, List
from ...interfaces.ai_interface import IAIProvider
from ...config.providers_config import ProvidersConfig
from ...utils.ai_utils import parse_ai_response, is_quota_error

class OpenRouterProvider(IAIProvider):
    """OpenRouter AI provider implementation"""
    
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name or ProvidersConfig.AI.OPENROUTER_MODEL
        self.max_tokens = ProvidersConfig.AI.OPENROUTER_MAX_TOKENS
        self.temperature = ProvidersConfig.AI.TEMPERATURE
        self.batch_size = ProvidersConfig.AI.OPENROUTER_BATCH_SIZE
        self.quota_exceeded = False
        self.last_error_time = None
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def generate_content(self, prompt: str, operation_type: str = "general") -> Optional[str]:
        """Generate content using OpenRouter"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ai-scholar.local",
                "X-Title": "AI Scholar Research Tool"
            }
            
            data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    content = result["choices"][0].get("message", {}).get("content", "").strip()
                    if content:
                        # Reset quota status on successful response
                        if self.quota_exceeded:
                            self.quota_exceeded = False
                            self.last_error_time = None
                        return content
            elif response.status_code == 429:
                self.quota_exceeded = True
                self.last_error_time = time.time()
                raise Exception("Rate limit exceeded")
            
            return None
            
        except Exception as e:
            if is_quota_error(e):
                self.quota_exceeded = True
                self.last_error_time = time.time()
            raise e
    
    def process_batch(self, prompt: str, batch_num: int, total_batches: int, operation_type: str) -> Optional[List[Dict[str, Any]]]:
        """Process a batch of papers with OpenRouter"""
        response_text = self.generate_content(prompt, f"{operation_type} batch")
        
        if not response_text:
            return None
        
        return parse_ai_response(response_text)
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "openrouter_horizon"
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        if self.quota_exceeded and self.last_error_time:
            # Check if cooldown period has passed
            cooldown_seconds = ProvidersConfig.AI.QUOTA_COOLDOWN_HOURS * 3600
            if time.time() - self.last_error_time > cooldown_seconds:
                self.quota_exceeded = False
                self.last_error_time = None
                return True
            return False
        
        return not self.quota_exceeded
    
    def get_optimal_batch_size(self, operation_type: str = "general") -> int:
        """Get optimal batch size for this provider"""
        base_size = self.batch_size
        return base_size + 5 if operation_type == "description" else base_size
    
    def reset_quota_status(self):
        """Reset quota exceeded status"""
        self.quota_exceeded = False
        self.last_error_time = None
