"""
Interaction Detector module.
Coordinates browser automation and DOM analysis to detect interactions.
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging

from ..browser.automation import BrowserAutomation
from ..models.schemas import (
    PageAnalysis, HoverInteraction, PopupInteraction, 
    ElementInfo, InteractionType
)
from .dom_analyzer import DOMAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InteractionDetector:
    """
    Detects and analyzes hover and popup interactions on a webpage.
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the interaction detector.
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout

    async def analyze_page(self, url: str) -> PageAnalysis:
        """
        Perform complete analysis of a webpage.
        
        Args:
            url: The URL to analyze
            
        Returns:
            PageAnalysis with all detected interactions
        """
        logger.info(f"Starting analysis of: {url}")
        
        async with BrowserAutomation(headless=self.headless, timeout=self.timeout) as browser:
            # Navigate to the page
            page_info = await browser.navigate(url)
            
            # Get page content for DOM analysis
            html_content = await browser.page.content()
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
        Detect all hover-based interactions on the page.
        """
        logger.info("Detecting hover interactions...")
        interactions = []
        
        # Get hoverable elements from browser
        hoverable_elements = await browser.find_hoverable_elements()
        
        # Get dropdown info from DOM analysis
        dropdown_info = dom_analyzer.find_dropdown_containers()
        
        # Combine information and test hovers
        tested_texts = set()
        
        for element in hoverable_elements[:15]:  # Limit to prevent long runs
            if not element.text_content:
                continue
                
            text_key = element.text_content.strip().lower()[:30]
            if text_key in tested_texts:
                continue
            tested_texts.add(text_key)
            
            logger.info(f"Testing hover on: {element.text_content[:50]}")
            
            interaction = await browser.simulate_hover(element)
            if interaction and (interaction.revealed_elements or interaction.revealed_links):
                interactions.append(interaction)
                logger.info(f"  Found {len(interaction.revealed_links)} revealed links")
            
            # Small delay between hovers
            await asyncio.sleep(0.3)
        
        # Also test dropdown triggers from DOM analysis
        for dropdown in dropdown_info[:5]:
            trigger_text = dropdown.get('trigger_text', '')
            if trigger_text and trigger_text.lower()[:30] not in tested_texts:
                tested_texts.add(trigger_text.lower()[:30])
                
                # Create element info for the dropdown trigger
                trigger_element = ElementInfo(
                    selector=f'text="{trigger_text}"',
                    tag_name='a',
                    text_content=trigger_text,
                    classes=[],
                    attributes={}
                )
                
                interaction = await browser.simulate_hover(trigger_element)
                if interaction:
                    # Enhance with DOM analysis data
                    for item in dropdown.get('items', []):
                        if not any(l.get('text') == item['text'] for l in interaction.revealed_links):
                            interaction.revealed_links.append(item)
                    
                    if interaction.revealed_links:
                        interactions.append(interaction)
        
        logger.info(f"Detected {len(interactions)} hover interactions")
        return interactions

    async def _detect_popup_interactions(
        self, 
        browser: BrowserAutomation, 
        dom_analyzer: DOMAnalyzer
    ) -> List[PopupInteraction]:
        """
        Detect all popup/modal interactions on the page.
        """
        logger.info("Detecting popup interactions...")
        interactions = []
        
        # Get clickable buttons from browser
        buttons = await browser.find_clickable_buttons()
        
        # Get modal triggers from DOM analysis
        modal_triggers = dom_analyzer.find_modal_triggers()
        
        tested_texts = set()
        
        # Test buttons that might trigger popups
        for button in buttons[:10]:  # Limit
            if not button.text_content:
                continue
            
            text = button.text_content.strip()
            text_key = text.lower()[:30]
            
            if text_key in tested_texts:
                continue
            tested_texts.add(text_key)
            
            # Prioritize buttons likely to trigger popups
            likely_popup = any(keyword in text.lower() for keyword in [
                'learn more', 'read more', 'continue', 'submit', 
                'sign up', 'subscribe', 'contact', 'external'
            ])
            
            # Check if it's in modal triggers
            is_modal_trigger = any(
                t.get('text', '').lower() == text.lower() 
                for t in modal_triggers
            )
            
            if likely_popup or is_modal_trigger:
                logger.info(f"Testing click on: {text[:50]}")
                
                interaction = await browser.simulate_click_for_popup(button)
                if interaction and interaction.popup_title:
                    interactions.append(interaction)
                    logger.info(f"  Found popup: {interaction.popup_title[:50]}")
                
                await asyncio.sleep(0.5)
        
        # Test external links that might show leaving warnings
        for trigger in modal_triggers[:5]:
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
                    
                    interaction = await browser.simulate_click_for_popup(trigger_element)
                    if interaction:
                        interactions.append(interaction)
        
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
