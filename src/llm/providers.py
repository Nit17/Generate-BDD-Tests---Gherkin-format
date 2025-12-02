"""
LLM Providers module.
Each provider class has a single responsibility (SRP).
Includes response caching to reduce API calls.
"""

import logging
import hashlib
from ..interfaces.llm import ILLMProvider
from ..utils.cache import llm_cache

logger = logging.getLogger(__name__)


def _generate_cache_key(provider: str, model: str, prompt: str) -> str:
    """Generate a cache key from provider, model, and prompt."""
    content = f"{provider}:{model}:{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


class OpenAIProvider(ILLMProvider):
    """
    OpenAI GPT provider implementation with caching.
    
    Follows:
    - SRP: Only handles OpenAI API communication
    - LSP: Can replace any ILLMProvider
    - OCP: Closed for modification, can be extended
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=api_key)
            self._model = model
            self._provider_name = "openai"
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    @property
    def provider_name(self) -> str:
        return self._provider_name
    
    @property
    def model_name(self) -> str:
        return self._model
    
    async def generate(self, prompt: str) -> str:
        """Generate response using OpenAI API with caching."""
        # Check cache first
        cache_key = _generate_cache_key(self._provider_name, self._model, prompt)
        cached = llm_cache.get(cache_key)
        if cached is not None:
            logger.info("Using cached LLM response")
            return cached
        
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert QA engineer specializing in BDD testing "
                        "and Gherkin syntax. Generate clean, well-formatted Gherkin "
                        "scenarios based on the provided webpage interaction data."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        result = response.choices[0].message.content
        
        # Cache the response
        llm_cache.put(cache_key, result)
        return result


class GeminiProvider(ILLMProvider):
    """
    Google Gemini provider implementation with caching.
    
    Follows:
    - SRP: Only handles Gemini API communication
    - LSP: Can replace any ILLMProvider
    - OCP: Closed for modification, can be extended
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model_instance = genai.GenerativeModel(model)
            self._model = model
            self._provider_name = "gemini"
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )
    
    @property
    def provider_name(self) -> str:
        return self._provider_name
    
    @property
    def model_name(self) -> str:
        return self._model
    
    async def generate(self, prompt: str) -> str:
        """Generate response using Gemini API with caching."""
        # Check cache first
        cache_key = _generate_cache_key(self._provider_name, self._model, prompt)
        cached = llm_cache.get(cache_key)
        if cached is not None:
            logger.info("Using cached LLM response")
            return cached
        
        system_prompt = (
            "You are an expert QA engineer specializing in BDD testing "
            "and Gherkin syntax. Generate clean, well-formatted Gherkin "
            "scenarios based on the provided webpage interaction data.\n\n"
        )
        response = await self._model_instance.generate_content_async(
            system_prompt + prompt
        )
        result = response.text
        
        # Cache the response
        llm_cache.put(cache_key, result)
        return result


class MockLLMProvider(ILLMProvider):
    """
    Mock LLM provider for testing.
    
    Follows LSP: Can replace any ILLMProvider in tests.
    """
    
    def __init__(self, response: str = ""):
        self._response = response
        self._provider_name = "mock"
        self._model = "mock-model"
    
    @property
    def provider_name(self) -> str:
        return self._provider_name
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def set_response(self, response: str) -> None:
        """Set the mock response."""
        self._response = response
    
    async def generate(self, prompt: str) -> str:
        """Return the mock response."""
        return self._response
