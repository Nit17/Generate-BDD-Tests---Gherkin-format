"""Browser automation interface - Dependency Inversion Principle."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..models.schemas import ElementInfo, HoverInteraction, PopupInteraction


class IBrowserAutomation(ABC):
    """
    Interface for browser automation.
    
    Following Interface Segregation Principle (ISP):
    - Only declares methods needed for browser automation
    - Clients depend on this interface, not concrete implementations
    """
    
    @abstractmethod
    async def start(self) -> None:
        """Start the browser instance."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the browser instance."""
        pass
    
    @abstractmethod
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL and return page metadata."""
        pass
    
    @abstractmethod
    async def get_page_content(self) -> str:
        """Get the current page HTML content."""
        pass
    
    @abstractmethod
    async def get_page_metadata(self) -> Dict[str, Any]:
        """Get metadata about the current page."""
        pass
    
    @abstractmethod
    async def find_hoverable_elements(self) -> List[ElementInfo]:
        """Find elements that can be hovered."""
        pass
    
    @abstractmethod
    async def simulate_hover(self, element: ElementInfo) -> Optional[HoverInteraction]:
        """Simulate hovering over an element."""
        pass
    
    @abstractmethod
    async def find_clickable_elements(self) -> List[ElementInfo]:
        """Find elements that can be clicked."""
        pass
    
    @abstractmethod
    async def simulate_click_for_popup(self, element: ElementInfo) -> Optional[PopupInteraction]:
        """Simulate clicking an element to trigger a popup."""
        pass
