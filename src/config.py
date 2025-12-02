"""
Centralized configuration for the BDD Test Generator.
Contains behavior thresholds and timing values only.
NO HARDCODED SELECTORS - all detection is dynamic and behavior-based.
"""

from dataclasses import dataclass
from typing import List
import os


@dataclass(frozen=True)
class BrowserConfig:
    """Browser automation configuration."""
    DEFAULT_TIMEOUT: int = 30000
    HEADLESS: bool = True
    VIEWPORT_WIDTH: int = 1920
    VIEWPORT_HEIGHT: int = 1080
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    PAGE_LOAD_WAIT: float = 3.0  # Increased for dynamic sites
    HOVER_WAIT: float = 0.5
    CLICK_WAIT: float = 0.5
    POPUP_CLOSE_WAIT: float = 0.3
    BETWEEN_ACTIONS_DELAY: float = 0.2
    ANIMATION_WAIT: float = 0.5  # Wait for CSS animations


@dataclass(frozen=True)
class DetectorConfig:
    """
    Dynamic element detection configuration.
    These are behavior thresholds, NOT hardcoded selectors.
    """
    # Element limits to prevent overwhelming (lower = faster)
    MAX_INTERACTIVE_ELEMENTS: int = 30
    MAX_HOVER_ELEMENTS: int = 15
    MAX_HOVERABLE_ELEMENTS: int = 15  # Alias
    MAX_CLICKABLE_ELEMENTS: int = 20
    MAX_POPUP_BUTTONS: int = 5
    MAX_CLICKABLE_BUTTONS: int = 5  # Alias
    MAX_NAV_ITEMS: int = 15
    MAX_REVEALED_LINKS: int = 10
    MAX_DROPDOWN_TRIGGERS: int = 10  # Max dropdown triggers to test
    MAX_MODAL_TRIGGERS: int = 10  # Max modal/popup triggers to test
    
    # Text limits
    TEXT_CONTENT_MAX_LENGTH: int = 200
    MAX_CSS_CLASSES: int = 10
    
    # Concurrency limits for parallel testing (higher = faster)
    CONCURRENT_HOVER_LIMIT: int = 5
    CONCURRENT_CLICK_LIMIT: int = 3
    
    # Behavior detection thresholds
    MIN_ELEMENT_WIDTH: int = 10  # Min width to consider visible
    MIN_ELEMENT_HEIGHT: int = 10  # Min height to consider visible
    MIN_POPUP_WIDTH: int = 200  # Min width to consider as popup
    MIN_POPUP_HEIGHT: int = 100  # Min height to consider as popup
    MIN_OVERLAY_ZINDEX: int = 100  # Min z-index to consider as overlay
    
    # DOM change detection
    MIN_DOM_CHANGES_FOR_EFFECT: int = 1  # Min new elements to consider hover effect


@dataclass(frozen=True)
class LLMConfig:
    """LLM provider configuration."""
    OPENAI_MODEL: str = "gpt-4"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 4000
    MAX_SCENARIOS: int = 10


@dataclass(frozen=True)
class OutputConfig:
    """Output configuration."""
    DEFAULT_OUTPUT_DIR: str = "./output"
    FEATURE_FILE_EXTENSION: str = ".feature"
    REPORT_FILE_EXTENSION: str = "_report.json"


# Global config instances
browser_config = BrowserConfig()
detector_config = DetectorConfig()
llm_config = LLMConfig()
output_config = OutputConfig()


# =============================================================================
# DEPRECATED: Legacy selectors kept for backward compatibility only
# These should NOT be used in new code - use DynamicElementDetector instead
# =============================================================================
class CSSSelectors:
    """
    DEPRECATED: These hardcoded selectors are kept only for backward compatibility.
    New code should use DynamicElementDetector for behavior-based detection.
    """
    HOVERABLE_ELEMENTS: str = "*"  # Detect all, filter by behavior
    CLICKABLE_BUTTONS: str = "*"   # Detect all, filter by behavior
    COOKIE_BANNERS: List[str] = [] # Dynamic detection
    COOKIE_BANNER_TEXT: List[str] = []
    POPUP_MODALS: str = "*"
    CLOSE_BUTTONS: str = "*"
    REVEALED_CONTENT: List[str] = []


css_selectors = CSSSelectors()
