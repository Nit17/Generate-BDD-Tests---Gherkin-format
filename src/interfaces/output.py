"""Output interfaces - Single Responsibility Principle."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.schemas import GherkinFeature, PageAnalysis


class IFeatureWriter(ABC):
    """
    Interface for writing feature files.
    
    Following Single Responsibility Principle (SRP):
    - Only responsible for writing feature files
    - Doesn't handle generation or analysis
    """
    
    @abstractmethod
    def write_feature(
        self, 
        feature: GherkinFeature, 
        filename: Optional[str] = None
    ) -> str:
        """Write a single feature to a file."""
        pass
    
    @abstractmethod
    def write_features(
        self, 
        features: List[GherkinFeature], 
        combined: bool = True,
        base_filename: Optional[str] = None
    ) -> List[str]:
        """Write multiple features to files."""
        pass
    
    @abstractmethod
    def write_from_analysis(
        self, 
        analysis: PageAnalysis, 
        feature_content: str
    ) -> str:
        """Write feature file from page analysis."""
        pass
