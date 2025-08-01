import time
import requests
from google import genai
from google.genai import types
from typing import Optional, Dict, Any, List
from .config import AIConfig
from .utils.ai_utils import parse_ai_response, is_quota_error

class AIModelManager:
    def __init__(self):
        self.models_config = {}
        self.current_model = None
        self._init_models()
    
    def _init_models(self):
        for i, api_key in enumerate(AIConfig.GOOGLE_API_KEYS):
            if api_key:
                key_name = f"key{i+1}"
                model_name = f"gemini-2.5-flash-lite-{key_name}"
                self.models_config[model_name] = {
                    "api_key": api_key,
                    "model_name": AIConfig.GEMINI_MODEL,
                    "max_tokens": AIConfig.GOOGLE_MAX_TOKENS,
                    "temperature": AIConfig.TEMPERATURE,
                    "enabled": True,
                    "quota_exceeded": False,
                    "last_error_time": None,
                    "priority": i + 1,
                    "batch_size": AIConfig.GOOGLE_BATCH_SIZE,
                    "key_name": key_name,
                    "provider": "google"
                }
        
        if AIConfig.OPENROUTER_API_KEY:
            self.models_config["horizon-alpha"] = {
                "api_key": AIConfig.OPENROUTER_API_KEY,
                "model_name": AIConfig.OPENROUTER_MODEL,
                "max_tokens": AIConfig.OPENROUTER_MAX_TOKENS,
                "temperature": AIConfig.TEMPERATURE,
                "enabled": True,
                "quota_exceeded": False,
                "last_error_time": None,
                "priority": 4,
                "batch_size": AIConfig.OPENROUTER_BATCH_SIZE,
                "key_name": "horizon",
                "provider": "openrouter"
            }
        
        if not self.models_config:
            raise ValueError("At least one API key required")
        
        self.available_models = list(self.models_config.keys())
        self.current_model = self.available_models[0]
    
    def get_optimal_batch_size(self, operation_type: str = "general") -> int:
        if self.current_model and self.current_model in self.models_config:
            base_size = self.models_config[self.current_model]["batch_size"]
            return base_size + 5 if operation_type == "description" else base_size
        return 30
    
    def _select_best_model(self) -> str:
        available = [
            (name, config) for name, config in self.models_config.items()
            if config["enabled"] and not config["quota_exceeded"]
        ]
        
        if not available:
            for name, config in self.models_config.items():
                if config["last_error_time"] and time.time() - config["last_error_time"] > AIConfig.QUOTA_COOLDOWN_HOURS * 3600:
                    config["quota_exceeded"] = False
            
            available = [
                (name, config) for name, config in self.models_config.items()
                if config["enabled"] and not config["quota_exceeded"]
            ]
        
        if available:
            best_model = min(available, key=lambda x: x[1]["priority"])
            self.current_model = best_model[0]
            return self.current_model
        else:
            return self.available_models[0]
    
    def _is_quota_error(self, error: Exception) -> bool:
        return is_quota_error(error)
    
    def _mark_model_quota_exceeded(self, model_name: str):
        if model_name in self.models_config:
            self.models_config[model_name]["quota_exceeded"] = True
            self.models_config[model_name]["last_error_time"] = time.time()
    
    def _generate_google_content(self, config: Dict, prompt: str) -> Optional[str]:
        client = genai.Client(api_key=config["api_key"])
        response = client.models.generate_content(
            model=config["model_name"],
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=config["temperature"],
                max_output_tokens=config["max_tokens"],
                top_p=AIConfig.TOP_P,
                top_k=AIConfig.TOP_K
            )
        )
        
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        return None
    
    def _generate_openrouter_content(self, config: Dict, prompt: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-scholar.local",
            "X-Title": "AI Scholar Research Tool"
        }
        
        data = {
            "model": config["model_name"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                return result["choices"][0].get("message", {}).get("content", "").strip()
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded")
        
        return None
    
    def generate_content(self, prompt: str, operation_type: str = "general") -> Optional[str]:
        attempts = 0
        max_attempts = len(self.available_models) + 1
        
        while attempts < max_attempts:
            try:
                current_model = self._select_best_model()
                config = self.models_config[current_model]
                
                if config["provider"] == "google":
                    response_text = self._generate_google_content(config, prompt)
                elif config["provider"] == "openrouter":
                    response_text = self._generate_openrouter_content(config, prompt)
                else:
                    raise Exception(f"Unknown provider: {config['provider']}")
                
                if response_text:
                    if config["quota_exceeded"]:
                        config["quota_exceeded"] = False
                        config["last_error_time"] = None
                    return response_text
                else:
                    raise Exception("Empty response")
                    
            except Exception as e:
                if self._is_quota_error(e):
                    self._mark_model_quota_exceeded(current_model)
                
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(AIConfig.RETRY_DELAY_SECONDS)
                else:
                    return None
        
        return None
    
    def process_batch(self, prompt: str, batch_num: int, total_batches: int, operation_type: str) -> Optional[List[Dict[str, Any]]]:
        response_text = self.generate_content(prompt, f"{operation_type} batch")
        
        if not response_text:
            return None
        
        return parse_ai_response(response_text)

ai_models = AIModelManager()