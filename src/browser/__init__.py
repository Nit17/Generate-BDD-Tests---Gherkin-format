"""Browser package for Playwright-based automation with dynamic detection."""

from .automation import BrowserAutomation
from .dynamic_detector import DynamicElementDetector

__all__ = ["BrowserAutomation", "DynamicElementDetector"]
