"""
Interaction Detector module.
Coordinates browser automation and DOM analysis to detect interactions.

Follows SOLID principles:
- SRP: Coordinates detection, delegates to specialized modules
- OCP: Detection strategies can be extended
- DIP: Depends on abstractions (IBrowserAutomation, IDOMAnalyzer)
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging

from ..interfaces.analyzer import IInteractionDetector
from ..interfaces.browser import IBrowserAutomation
from ..browser.automation import BrowserAutomation
from ..models.schemas import (
    PageAnalysis, HoverInteraction, PopupInteraction, 
    ElementInfo, InteractionType
)
from .dom_analyzer import DOMAnalyzer
from ..config import detector_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Concurrency control for parallel operations
MAX_CONCURRENT_HOVERS = detector_config.MAX_HOVER_ELEMENTS
MAX_CONCURRENT_CLICKS = detector_config.MAX_POPUP_BUTTONS


class InteractionDetector(IInteractionDetector):
    """
    Detects and analyzes hover and popup interactions on a webpage.
    
    Follows:
    - SRP: Coordinates detection workflow
    - OCP: New detection strategies can be added
    - DIP: Can accept injected browser automation for testing
    """

    def __init__(
        self, 
        headless: bool = True, 
        timeout: int = 30000,
        browser_automation: Optional[IBrowserAutomation] = None
    ):
        """
        Initialize the interaction detector.
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
            browser_automation: Optional injected browser automation (for DIP)
        """
        self.headless = headless
        self.timeout = timeout
        self._injected_browser = browser_automation

    def _create_browser(self) -> BrowserAutomation:
        """Create browser instance. Allows injection for testing (DIP)."""
        if self._injected_browser:
            return self._injected_browser
        return BrowserAutomation(headless=self.headless, timeout=self.timeout)

    async def analyze_page(self, url: str) -> PageAnalysis:
        """
        Perform complete analysis of a webpage.
        
        Args:
            url: The URL to analyze
            
        Returns:
            PageAnalysis with all detected interactions
        """
        logger.info(f"Starting analysis of: {url}")
        
        browser = self._create_browser()
        
        async with browser:
            # Navigate to the page
            page_info = await browser.navigate(url)
            
            # Get page content for DOM analysis
            html_content = await browser.get_page_content()
            dom_analyzer = DOMAnalyzer(html_content)
            
            # Get page metadata
            metadata = await browser.get_page_metadata()
            metadata.update(dom_analyzer.get_page_structure_summary())
            
            # Detect hover interactions
            hover_interactions = await self._detect_hover_interactions(browser, dom_analyzer)
            
            # Detect popup interactions
            popup_interactions = await self._detect_popup_interactions(browser, dom_analyzer)
            
            # Get navigation elements
            navigation_elements = await self._get_navigation_elements(browser)
            
            return PageAnalysis(
                url=url,
                page_title=page_info.get('title', ''),
                hover_interactions=hover_interactions,
                popup_interactions=popup_interactions,
                navigation_elements=navigation_elements,
                metadata=metadata
            )

    async def _detect_hover_interactions(
        self, 
        browser: BrowserAutomation,
        dom_analyzer: DOMAnalyzer
    ) -> List[HoverInteraction]:
        """
        Detect all hover-based interactions on the page using parallel execution.
        Uses semaphore to control concurrency.
        """
        logger.info("Detecting hover interactions with parallel execution...")
        
        # Get hoverable elements from browser
        hoverable_elements = await browser.find_hoverable_elements()
        
        # Get dropdown info from DOM analysis
        dropdown_info = dom_analyzer.find_dropdown_containers()
        
        # Build list of unique elements to test
        elements_to_test: List[ElementInfo] = []
        tested_texts = set()
        
        # Add browser-detected hoverable elements
        for element in hoverable_elements[:MAX_CONCURRENT_HOVERS]:
            if not element.text_content:
                continue
            text_key = element.text_content.strip().lower()[:30]
            if text_key not in tested_texts:
                tested_texts.add(text_key)
                elements_to_test.append(element)
        
        # Add dropdown triggers from DOM analysis
        for dropdown in dropdown_info[:detector_config.MAX_DROPDOWN_TRIGGERS]:
            trigger_text = dropdown.get('trigger_text', '')
            if trigger_text and trigger_text.lower()[:30] not in tested_texts:
                tested_texts.add(trigger_text.lower()[:30])
                trigger_element = ElementInfo(
                    selector=f'text="{trigger_text}"',
                    tag_name='a',
                    text_content=trigger_text,
                    classes=[],
                    attributes={}
                )
                elements_to_test.append(trigger_element)
        
        # Test hovers in parallel with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent hover tests
        
        async def test_hover_with_semaphore(element: ElementInfo) -> Optional[HoverInteraction]:
            async with semaphore:
                logger.info(f"Testing hover on: {element.text_content[:50]}")
                interaction = await browser.simulate_hover(element)
                if interaction and (interaction.revealed_elements or interaction.revealed_links):
                    logger.info(f"  Found {len(interaction.revealed_links)} revealed links")
                    return interaction
                return None
        
        # Run all hover tests in parallel
        results = await asyncio.gather(
            *[test_hover_with_semaphore(el) for el in elements_to_test],
            return_exceptions=True
        )
        
        # Collect successful interactions
        interactions = []
        for result in results:
            if isinstance(result, HoverInteraction):
                interactions.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Hover test failed: {result}")
        
        logger.info(f"Detected {len(interactions)} hover interactions")
        return interactions

    async def _detect_popup_interactions(
        self, 
        browser: BrowserAutomation, 
        dom_analyzer: DOMAnalyzer
    ) -> List[PopupInteraction]:
        """
        Detect all popup/modal interactions on the page using parallel execution.
        """
        logger.info("Detecting popup interactions with parallel execution...")
        
        # Get clickable buttons from browser
        buttons = await browser.find_clickable_buttons()
        
        # Get modal triggers from DOM analysis
        modal_triggers = dom_analyzer.find_modal_triggers()
        
        # Build list of elements to test - ALL clickable buttons are candidates
        # No hardcoded keywords - the dynamic detector already filtered by behavior
        elements_to_test: List[ElementInfo] = []
        tested_texts = set()
        
        # All buttons from dynamic detection are already likely to trigger interactions
        for button in buttons[:MAX_CONCURRENT_CLICKS]:
            if not button.text_content:
                continue
            
            text = button.text_content.strip()
            text_key = text.lower()[:30]
            
            if text_key in tested_texts:
                continue
            
            tested_texts.add(text_key)
            elements_to_test.append(button)
        
        # Add external links that might show leaving warnings
        for trigger in modal_triggers[:detector_config.MAX_MODAL_TRIGGERS]:
            text = trigger.get('text', '')
            if trigger.get('type') == 'external_link' and text:
                text_key = text.lower()[:30]
                if text_key not in tested_texts:
                    tested_texts.add(text_key)
                    trigger_element = ElementInfo(
                        selector=f'text="{text}"',
                        tag_name='a',
                        text_content=text,
                        classes=[],
                        attributes={'href': trigger.get('href', '')}
                    )
                    elements_to_test.append(trigger_element)
        
        # Test clicks in parallel with controlled concurrency
        semaphore = asyncio.Semaphore(2)  # Max 2 concurrent click tests (popups need more isolation)
        
        async def test_click_with_semaphore(element: ElementInfo) -> Optional[PopupInteraction]:
            async with semaphore:
                text = element.text_content[:50] if element.text_content else "unknown"
                logger.info(f"Testing click on: {text}")
                interaction = await browser.simulate_click_for_popup(element)
                if interaction and interaction.popup_title:
                    logger.info(f"  Found popup: {interaction.popup_title[:50]}")
                    return interaction
                return None
        
        # Run all click tests in parallel
        results = await asyncio.gather(
            *[test_click_with_semaphore(el) for el in elements_to_test],
            return_exceptions=True
        )
        
        # Collect successful interactions
        interactions = []
        for result in results:
            if isinstance(result, PopupInteraction):
                interactions.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Click test failed: {result}")
        
        logger.info(f"Detected {len(interactions)} popup interactions")
        return interactions

    async def _get_navigation_elements(self, browser: BrowserAutomation) -> List[ElementInfo]:
        """
        Get navigation elements from the page.
        """
        nav_structure = await browser.get_navigation_structure()
        
        elements = []
        for item in nav_structure[:20]:
            elements.append(ElementInfo(
                selector=f'a[href="{item.get("href", "")}"]',
                tag_name='a',
                text_content=item.get('text', ''),
                classes=[],
                attributes={
                    'href': item.get('href', ''),
                    'has_dropdown': str(item.get('hasDropdown', False))
                }
            ))
        
        return elements

    async def quick_scan(self, url: str) -> Dict[str, Any]:
        """
        Perform a quick scan of a page without full interaction testing.
        
        Args:
            url: The URL to scan
            
        Returns:
            Quick overview of the page's interactive elements
        """
        async with BrowserAutomation(headless=self.headless, timeout=self.timeout) as browser:
            await browser.navigate(url)
            
            html_content = await browser.page.content()
            dom_analyzer = DOMAnalyzer(html_content)
            
            return dom_analyzer.extract_all_interactions()
