"""LLM interfaces - Open/Closed Principle."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.schemas import PageAnalysis, GherkinFeature


class ILLMProvider(ABC):
    """
    Interface for LLM providers.
    
    Following Open/Closed Principle (OCP):
    - Open for extension: New LLM providers can be added
    - Closed for modification: Existing code doesn't need to change
    
    Following Liskov Substitution Principle (LSP):
    - Any implementation can replace ILLMProvider
    """
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate text from a prompt."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        pass


class IGherkinGenerator(ABC):
    """
    Interface for Gherkin generation.
    
    Following Single Responsibility Principle (SRP):
    - Only responsible for generating Gherkin content
    - Delegates LLM calls to ILLMProvider
    """
    
    @abstractmethod
    async def generate_features(self, analysis: PageAnalysis) -> List[GherkinFeature]:
        """Generate Gherkin features from page analysis."""
        pass
    
    @abstractmethod
    async def generate_combined_feature(self, analysis: PageAnalysis) -> str:
        """Generate combined feature file content."""
        pass
