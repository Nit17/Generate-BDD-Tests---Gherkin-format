"""
LLM Providers module.
Each provider class has a single responsibility (SRP).
"""

import logging
from ..interfaces.llm import ILLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(ILLMProvider):
    """
    OpenAI GPT provider implementation.
    
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
        """Generate response using OpenAI API."""
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
        return response.choices[0].message.content


class GeminiProvider(ILLMProvider):
    """
    Google Gemini provider implementation.
    
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
        """Generate response using Gemini API."""
        system_prompt = (
            "You are an expert QA engineer specializing in BDD testing "
            "and Gherkin syntax. Generate clean, well-formatted Gherkin "
            "scenarios based on the provided webpage interaction data.\n\n"
        )
        response = await self._model_instance.generate_content_async(
            system_prompt + prompt
        )
        return response.text


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
