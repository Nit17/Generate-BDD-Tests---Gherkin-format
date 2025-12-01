"""
Factory module for creating instances with dependency injection.
Follows Dependency Inversion Principle (DIP).
"""

import os
from typing import Optional
from .interfaces import (
    IBrowserAutomation, IDOMAnalyzer, IInteractionDetector,
    ILLMProvider, IGherkinGenerator, IFeatureWriter
)
from .browser.automation import BrowserAutomation
from .analyzer.dom_analyzer import DOMAnalyzer
from .analyzer.interaction_detector import InteractionDetector
from .llm.gherkin_generator import GherkinGenerator
from .llm.providers import OpenAIProvider, GeminiProvider
from .output.feature_writer import FeatureWriter


class ServiceFactory:
    """
    Factory for creating service instances.
    
    Implements Dependency Inversion Principle:
    - High-level modules don't depend on low-level modules
    - Both depend on abstractions
    """
    
    @staticmethod
    def create_browser_automation(
        headless: bool = True, 
        timeout: int = 10000
    ) -> IBrowserAutomation:
        """Create a browser automation instance."""
        return BrowserAutomation(headless=headless, timeout=timeout)
    
    @staticmethod
    def create_dom_analyzer(html_content: str) -> IDOMAnalyzer:
        """Create a DOM analyzer instance."""
        return DOMAnalyzer(html_content=html_content)
    
    @staticmethod
    def create_interaction_detector(
        headless: bool = True, 
        timeout: int = 30000
    ) -> IInteractionDetector:
        """Create an interaction detector instance."""
        return InteractionDetector(headless=headless, timeout=timeout)
    
    @staticmethod
    def create_llm_provider(
        provider: str = "openai",
        api_key: Optional[str] = None
    ) -> ILLMProvider:
        """
        Create an LLM provider instance.
        
        Following Open/Closed Principle:
        - Easy to add new providers without modifying existing code
        """
        provider = provider.lower()
        
        if api_key is None:
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                f"API key required for {provider}. "
                f"Set {provider.upper()}_API_KEY environment variable."
            )
        
        if provider == "openai":
            return OpenAIProvider(api_key=api_key)
        elif provider == "gemini":
            return GeminiProvider(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'gemini'.")
    
    @staticmethod
    def create_gherkin_generator(
        provider: str = "openai",
        api_key: Optional[str] = None,
        llm_provider: Optional[ILLMProvider] = None
    ) -> IGherkinGenerator:
        """
        Create a Gherkin generator instance.
        
        Following Dependency Inversion:
        - Can inject ILLMProvider for testing
        """
        if llm_provider is None:
            llm_provider = ServiceFactory.create_llm_provider(provider, api_key)
        return GherkinGenerator(llm_provider=llm_provider)
    
    @staticmethod
    def create_feature_writer(output_dir: str = "./output") -> IFeatureWriter:
        """Create a feature writer instance."""
        return FeatureWriter(output_dir=output_dir)
