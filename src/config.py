"""
Centralized configuration for the BDD Test Generator.
All magic numbers and configurable values are defined here.
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
    PAGE_LOAD_WAIT: float = 2.0
    HOVER_WAIT: float = 0.5
    CLICK_WAIT: float = 1.0
    POPUP_CLOSE_WAIT: float = 0.5
    BETWEEN_ACTIONS_DELAY: float = 0.3


@dataclass(frozen=True)
class DetectorConfig:
    """Element detection configuration."""
    MAX_ELEMENTS_PER_SELECTOR: int = 20
    MAX_HOVER_ELEMENTS: int = 15
    MAX_HOVERABLE_ELEMENTS: int = 15  # Alias for compatibility
    MAX_POPUP_BUTTONS: int = 10
    MAX_CLICKABLE_BUTTONS: int = 10  # Alias for compatibility
    MAX_DROPDOWN_TRIGGERS: int = 5
    MAX_MODAL_TRIGGERS: int = 5
    MAX_NAV_ITEMS: int = 30
    MAX_REVEALED_LINKS: int = 10
    TEXT_CONTENT_MAX_LENGTH: int = 200
    MAX_CSS_CLASSES: int = 10
    CONCURRENT_HOVER_LIMIT: int = 3
    CONCURRENT_CLICK_LIMIT: int = 2
    
    # Keywords that indicate popup-triggering buttons
    POPUP_KEYWORDS: tuple = (
        'learn more', 'read more', 'continue', 'submit',
        'sign up', 'subscribe', 'contact', 'external'
    )


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


# Combined CSS selectors for better performance
class CSSSelectors:
    """Pre-combined CSS selectors for efficient querying."""
    
    HOVERABLE_ELEMENTS: str = ", ".join([
        "nav a", "nav button", "nav li",
        "header a", "header button",
        "[class*='nav'] a", "[class*='menu'] a", "[class*='dropdown']",
        "[role='navigation'] a", "[role='menuitem']",
        "a[class*='hover']", "[class*='tooltip']",
        "[aria-haspopup='true']", "[aria-expanded]",
        ".nav-item", ".menu-item", ".dropdown-toggle",
        "[data-toggle='dropdown']", "[data-bs-toggle='dropdown']"
    ])
    
    CLICKABLE_BUTTONS: str = ", ".join([
        "button", "a.btn", "a.button", ".btn", ".button",
        "[role='button']", "input[type='button']", "input[type='submit']",
        "[class*='cta']", "[class*='learn-more']", "[class*='read-more']",
        "a[target='_blank']", "[data-modal]", "[data-popup]",
        "[class*='modal-trigger']", "[class*='popup-trigger']"
    ])
    
    COOKIE_BANNERS: List[str] = [
        "#onetrust-accept-btn-handler",
        ".onetrust-accept-btn-handler",
        "[id*='accept'][id*='cookie']",
        "[class*='accept'][class*='cookie']",
        "button[aria-label*='Accept']",
        "button[aria-label*='accept']",
        "#accept-cookies",
        ".accept-cookies",
        "[data-testid='cookie-accept']",
        ".cookie-consent-accept",
        "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        ".cc-accept",
        "#cookie-accept",
    ]
    
    # Text-based selectors (can't be combined)
    COOKIE_BANNER_TEXT: List[str] = [
        "Accept All",
        "Accept Cookies", 
        "I Accept",
        "OK",
        "Agree",
    ]
    
    POPUP_MODALS: str = ", ".join([
        ".modal:not([style*='display: none'])",
        ".popup:not([style*='display: none'])",
        "[role='dialog']:not([style*='display: none'])",
        ".overlay:not([style*='display: none'])",
        "[class*='modal']:not([style*='display: none'])",
        "[class*='popup']:not([style*='display: none'])",
        "[class*='dialog']:not([style*='display: none'])",
        ".ReactModal__Content",
        "[aria-modal='true']"
    ])
    
    CLOSE_BUTTONS: str = ", ".join([
        ".modal .close", ".popup .close", "[aria-label='Close']",
        ".modal-close", ".popup-close", "button.close",
        "[class*='close']", ".dismiss", ".cancel"
    ])
    
    REVEALED_CONTENT: List[str] = [
        ".dropdown-menu:visible", ".submenu:visible",
        "[class*='dropdown']:not([style*='display: none'])",
        "[class*='submenu']:not([style*='display: none'])",
        "[aria-expanded='true'] + *"
    ]


# Popup trigger keywords
POPUP_TRIGGER_KEYWORDS: List[str] = [
    "learn more", "read more", "continue", "submit",
    "sign up", "subscribe", "contact", "external"
]


# Global config instances
browser_config = BrowserConfig()
detector_config = DetectorConfig()
llm_config = LLMConfig()
output_config = OutputConfig()
css_selectors = CSSSelectors()
