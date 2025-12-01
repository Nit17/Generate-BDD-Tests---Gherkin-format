"""Analyzer interfaces - Interface Segregation Principle."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..models.schemas import PageAnalysis


class IDOMAnalyzer(ABC):
    """
    Interface for DOM analysis.
    
    Following Single Responsibility Principle (SRP):
    - Only responsible for analyzing DOM structure
    - Doesn't handle browser automation or output generation
    """
    
    @abstractmethod
    def find_navigation_menus(self) -> List[Dict[str, Any]]:
        """Find navigation menus in the DOM."""
        pass
    
    @abstractmethod
    def find_interactive_elements(self) -> List[Dict[str, Any]]:
        """Find interactive elements like buttons and links."""
        pass
    
    @abstractmethod
    def find_dropdown_containers(self) -> List[Dict[str, Any]]:
        """Find dropdown/submenu containers."""
        pass
    
    @abstractmethod
    def find_modal_triggers(self) -> List[Dict[str, Any]]:
        """Find elements that trigger modals/popups."""
        pass
    
    @abstractmethod
    def get_page_structure_summary(self) -> Dict[str, Any]:
        """Get a summary of the page structure."""
        pass


class IInteractionDetector(ABC):
    """
    Interface for detecting page interactions.
    
    Following Dependency Inversion Principle (DIP):
    - Depends on IBrowserAutomation and IDOMAnalyzer abstractions
    - Not on concrete implementations
    """
    
    @abstractmethod
    async def analyze_page(self, url: str) -> PageAnalysis:
        """Perform complete analysis of a webpage."""
        pass
