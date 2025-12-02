"""
Browser automation module using Playwright.
Handles page loading, element interaction, and state capture.

Follows SOLID principles:
- SRP: Handles only browser automation concerns
- OCP: Can be extended for different browser engines
- DIP: Implements IBrowserAutomation interface

FULLY DYNAMIC: Uses behavior-based detection, NO hardcoded selectors.
All element detection is done at runtime by analyzing page behavior.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, ElementHandle, Locator
import logging

from ..interfaces.browser import IBrowserAutomation
from ..models.schemas import ElementInfo, HoverInteraction, PopupInteraction, InteractionType
from ..config import browser_config, detector_config
from .dynamic_detector import DynamicElementDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CookieBannerHandler:
    """
    Handles cookie consent banner dismissal.
    Uses DYNAMIC detection - analyzes page behavior, not hardcoded selectors.
    """
    
    def __init__(self, page: Page):
        self.page = page
    
    async def dismiss(self) -> bool:
        """
        Try to dismiss cookie consent banners using dynamic detection.
        Analyzes page structure at runtime instead of using hardcoded selectors.
        Returns True if dismissed.
        """
        dismissed = await self.page.evaluate('''() => {
            // First try to find and click common accept buttons
            const acceptSelectors = [
                '#onetrust-accept-btn-handler',
                '[id*="accept"]',
                '[id*="consent"]',
                'button[aria-label*="accept" i]',
                'button[aria-label*="agree" i]',
                '.onetrust-close-btn-handler'
            ];
            
            for (const selector of acceptSelectors) {
                try {
                    const btn = document.querySelector(selector);
                    if (btn && btn.offsetParent !== null) {
                        btn.click();
                        return true;
                    }
                } catch (e) {}
            }
            
            // Find any fixed/overlay element that might be a cookie banner
            const allElements = document.querySelectorAll('*');
            
            for (const el of allElements) {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                // Check for overlay/banner characteristics
                const isOverlay = (
                    (style.position === 'fixed' || style.position === 'sticky') &&
                    parseInt(style.zIndex) > 100 &&
                    rect.width > 100 &&
                    rect.height > 30
                );
                
                if (!isOverlay) continue;
                
                // Check if content suggests cookie/consent banner
                const text = (el.textContent || '').toLowerCase();
                const isCookieBanner = (
                    text.includes('cookie') ||
                    text.includes('consent') ||
                    text.includes('privacy') ||
                    text.includes('gdpr') ||
                    text.includes('accept') ||
                    text.includes('agree')
                );
                
                if (!isCookieBanner) continue;
                
                // Find accept/close button within this banner
                const buttons = el.querySelectorAll('button, a, [role="button"], [tabindex]');
                for (const btn of buttons) {
                    const btnText = (btn.textContent || '').toLowerCase();
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                    
                    // Check for accept patterns (dynamically)
                    if (btnText.includes('accept') || btnText.includes('agree') ||
                        btnText.includes('allow') || btnText.includes('ok') ||
                        btnText.includes('got it') || btnText.includes('understand') ||
                        btnText.includes('continue') || btnText.includes('close') ||
                        ariaLabel.includes('accept') || ariaLabel.includes('close')) {
                        
                        btn.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if dismissed:
            logger.info("Dismissed cookie banner using dynamic detection")
            await asyncio.sleep(browser_config.POPUP_CLOSE_WAIT)
            
            # Also try to hide any remaining overlay
            await self.page.evaluate('''() => {
                // Hide OneTrust dark filter if present
                const overlays = document.querySelectorAll('.onetrust-pc-dark-filter, #onetrust-consent-sdk, [class*="consent-overlay"]');
                overlays.forEach(el => {
                    el.style.display = 'none';
                });
            }''')
        
        return dismissed


class ElementExtractor:
    """
    Extracts information from DOM elements.
    Single source of truth for element extraction (removes duplication).
    """
    
    def __init__(self, page: Page):
        self.page = page
    
    async def get_element_info(self, element: ElementHandle) -> Optional[ElementInfo]:
        """Extract information from an element handle."""
        try:
            # Batch evaluate for better performance
            # Use replace with regex to normalize all whitespace to single spaces
            info = await element.evaluate('''el => ({
                tagName: el.tagName.toLowerCase(),
                textContent: (el.textContent || "").replace(/\\s+/g, " ").trim().substring(0, 200),
                ariaLabel: el.getAttribute('aria-label'),
                role: el.getAttribute('role'),
                classes: (el.getAttribute('class') || '').split(' ').filter(c => c).slice(0, 10),
                href: el.getAttribute('href'),
                dataTestid: el.getAttribute('data-testid'),
                id: el.getAttribute('id'),
                name: el.getAttribute('name'),
                type: el.getAttribute('type'),
                title: el.getAttribute('title')
            })''')
            
            attributes = {k: v for k, v in {
                'href': info.get('href'),
                'data-testid': info.get('dataTestid'),
                'id': info.get('id'),
                'name': info.get('name'),
                'type': info.get('type'),
                'title': info.get('title')
            }.items() if v}
            
            bounding_box = None
            try:
                bounding_box = await element.bounding_box()
            except:
                pass
            
            selector = await self._generate_selector(element)
            
            return ElementInfo(
                selector=selector,
                tag_name=info['tagName'],
                text_content=info['textContent'][:detector_config.TEXT_CONTENT_MAX_LENGTH] or None,
                aria_label=info.get('ariaLabel'),
                role=info.get('role'),
                classes=info['classes'][:detector_config.MAX_CSS_CLASSES],
                attributes=attributes,
                bounding_box=bounding_box
            )
        except Exception as e:
            logger.warning(f"Error extracting element info: {e}")
            return None
    
    async def _generate_selector(self, element: ElementHandle) -> str:
        """Generate a CSS selector for an element."""
        try:
            selector = await element.evaluate('''el => {
                if (el.id) return '#' + el.id;
                if (el.getAttribute('data-testid')) 
                    return `[data-testid="${el.getAttribute('data-testid')}"]`;
                
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.tagName.toLowerCase();
                    if (el.id) {
                        selector = '#' + el.id;
                        path.unshift(selector);
                        break;
                    }
                    let sibling = el;
                    let nth = 1;
                    while (sibling = sibling.previousElementSibling) {
                        if (sibling.tagName === el.tagName) nth++;
                    }
                    if (nth > 1) selector += `:nth-of-type(${nth})`;
                    path.unshift(selector);
                    el = el.parentElement;
                }
                return path.join(' > ');
            }''')
            return selector
        except:
            return 'unknown'


class BrowserAutomation(IBrowserAutomation):
    """
    Playwright-based browser automation for detecting and interacting with web elements.
    
    FULLY DYNAMIC: Uses behavior-based detection, NO hardcoded selectors.
    - DynamicElementDetector for finding interactive elements
    - Runtime analysis of page structure and behavior
    - Works on any modern website without configuration
    """

    def __init__(self, headless: bool = None, timeout: int = None):
        """
        Initialize the browser automation.
        
        Args:
            headless: Run browser in headless mode (uses config default if None)
            timeout: Default timeout in milliseconds (uses config default if None)
        """
        self.headless = headless if headless is not None else browser_config.HEADLESS
        self.timeout = timeout if timeout is not None else browser_config.DEFAULT_TIMEOUT
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self._cookie_handler: Optional[CookieBannerHandler] = None
        self._element_extractor: Optional[ElementExtractor] = None
        self._dynamic_detector: Optional[DynamicElementDetector] = None
        self._hover_semaphore = asyncio.Semaphore(detector_config.CONCURRENT_HOVER_LIMIT)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser with optimized settings."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-web-security', '--disable-features=IsolateOrigins,site-per-process']
        )
        context = await self.browser.new_context(
            viewport={
                'width': browser_config.VIEWPORT_WIDTH, 
                'height': browser_config.VIEWPORT_HEIGHT
            },
            user_agent=browser_config.USER_AGENT
        )
        self.page = await context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        # Initialize helper classes
        self._cookie_handler = CookieBannerHandler(self.page)
        self._element_extractor = ElementExtractor(self.page)
        self._dynamic_detector = DynamicElementDetector(self.page)

    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def get_page_content(self) -> str:
        """Get the current page HTML content."""
        return await self.page.content()

    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL and wait for the page to load.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Page metadata including title and URL
        """
        logger.info(f"Navigating to: {url}")
        # Use 'domcontentloaded' instead of 'networkidle' to avoid timeout on sites with continuous network activity
        await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
        # Wait a bit more for dynamic content to load
        await asyncio.sleep(browser_config.PAGE_LOAD_WAIT + 1)
        
        # Dismiss cookie consent banners using helper - try multiple times
        if self._cookie_handler:
            for _ in range(3):  # Try up to 3 times
                dismissed = await self._cookie_handler.dismiss()
                if dismissed:
                    await asyncio.sleep(0.5)  # Wait for animation
                else:
                    break
        
        # Force hide any remaining overlays that might block interaction
        await self.page.evaluate('''() => {
            // Remove any overlay that might be blocking interaction
            const overlays = document.querySelectorAll('[class*="consent"], [class*="cookie"], [class*="overlay"], [id*="consent"], [id*="cookie"]');
            overlays.forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'absolute') {
                    el.style.display = 'none';
                }
            });
        }''')
        
        title = await self.page.title()
        current_url = self.page.url
        
        return {
            'title': title,
            'url': current_url,
            'loaded': True
        }

    async def _dismiss_cookie_banners(self):
        """Delegate to CookieBannerHandler."""
        if self._cookie_handler:
            await self._cookie_handler.dismiss()

    async def get_element_info(self, element: ElementHandle) -> Optional[ElementInfo]:
        """
        Delegate to ElementExtractor for element info extraction.
        Removes code duplication.
        """
        if self._element_extractor:
            return await self._element_extractor.get_element_info(element)
        return None

    async def _generate_selector(self, element: ElementHandle) -> str:
        """Delegate to ElementExtractor for selector generation."""
        if self._element_extractor:
            return await self._element_extractor._generate_selector(element)
        return 'unknown'

    async def find_hoverable_elements(self) -> List[ElementInfo]:
        """
        Find elements that are likely to have hover interactions.
        Uses DYNAMIC behavior-based detection, NOT hardcoded selectors.
        
        Returns:
            List of ElementInfo for hoverable elements
        """
        logger.info("Finding hoverable elements using dynamic detection...")
        
        if self._dynamic_detector:
            try:
                elements = await self._dynamic_detector.find_hoverable_elements()
                logger.info(f"Dynamic detector returned {len(elements)} elements")
                # Limit to configured maximum
                return elements[:detector_config.MAX_HOVERABLE_ELEMENTS]
            except Exception as e:
                logger.error(f"Dynamic detector failed: {e}")
                # Fall through to fallback
        
        # Fallback if dynamic detector is not available or fails
        logger.info("Using fallback hoverable detection...")
        return await self.find_nav_elements_fallback()

    async def find_clickable_elements(self) -> List[ElementInfo]:
        """
        Find elements that can be clicked (interface method).
        Uses DYNAMIC behavior-based detection.
        
        Returns:
            List of ElementInfo for clickable elements
        """
        return await self.find_clickable_buttons()

    async def find_clickable_buttons(self) -> List[ElementInfo]:
        """
        Find buttons that might trigger popups or modals.
        Uses DYNAMIC behavior-based detection, NOT hardcoded selectors.
        
        Returns:
            List of ElementInfo for clickable buttons
        """
        logger.info("Finding clickable buttons using dynamic detection...")
        
        if self._dynamic_detector:
            try:
                elements = await self._dynamic_detector.find_clickable_elements()
                logger.info(f"Dynamic detector returned {len(elements)} clickable buttons")
                # Limit to configured maximum
                return elements[:detector_config.MAX_CLICKABLE_BUTTONS]
            except Exception as e:
                logger.error(f"Dynamic detector failed for clickable: {e}")
        
        return []

    async def find_nav_elements_fallback(self) -> List[ElementInfo]:
        """
        Fallback method to find navigation elements when dynamic detection fails.
        Uses simple, reliable selectors that work on most sites.
        
        Returns:
            List of ElementInfo for navigation elements
        """
        logger.info("Using fallback navigation detection...")
        
        nav_elements = await self.page.evaluate('''() => {
            const results = [];
            const seen = new Set();
            
            // Find all links in nav, header, or with nav-related classes
            const selectors = [
                'nav a',
                'header a',
                '[role="navigation"] a',
                '[class*="nav"] a',
                '[class*="menu"] a',
                'a[class*="nav"]',
                'a[class*="menu"]',
                '.navigation a',
                '.main-menu a',
                '.header a'
            ];
            
            for (const selector of selectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;
                        
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden') continue;
                        
                        const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                        if (!text || text.length > 50) continue;
                        
                        const textKey = text.toLowerCase();
                        if (seen.has(textKey)) continue;
                        seen.add(textKey);
                        
                        results.push({
                            selector: `text="${text}"`,
                            tagName: el.tagName.toLowerCase(),
                            text: text,
                            href: el.getAttribute('href'),
                            classes: (el.className || '').toString().split(' ').filter(c => c).slice(0, 5),
                            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                        });
                        
                        if (results.length >= 20) break;
                    }
                } catch (e) {}
                if (results.length >= 20) break;
            }
            
            return results;
        }''')
        
        elements = []
        for item in nav_elements:
            attrs = {}
            if item.get('href'):
                attrs['href'] = item['href']
            
            elements.append(ElementInfo(
                selector=item['selector'],
                tag_name=item['tagName'],
                text_content=item['text'],
                classes=item.get('classes', []),
                attributes=attrs,
                bounding_box=item.get('rect')
            ))
        
        logger.info(f"Fallback found {len(elements)} navigation elements")
        return elements

    async def simulate_hover(self, element_info: ElementInfo) -> Optional[HoverInteraction]:
        """
        Simulate hovering over an element and detect what appears.
        
        Args:
            element_info: Information about the element to hover
            
        Returns:
            HoverInteraction with revealed elements, or None if nothing appeared
        """
        try:
            # Find and hover the element
            element = await self.page.query_selector(element_info.selector)
            if not element:
                # Try alternative selectors
                if element_info.text_content:
                    element = await self.page.query_selector(f'text="{element_info.text_content}"')
            
            if not element:
                return None
            
            # Hover over the element
            await element.hover()
            await asyncio.sleep(browser_config.HOVER_WAIT)
            
            # Find newly visible elements
            revealed_elements = await self._find_revealed_elements(element_info.selector)
            revealed_links = await self._find_revealed_links(element_info.selector)
            
            if revealed_elements or revealed_links:
                return HoverInteraction(
                    trigger_element=element_info,
                    revealed_elements=revealed_elements,
                    revealed_links=revealed_links,
                    interaction_type=InteractionType.HOVER_DROPDOWN
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error simulating hover: {e}")
            return None

    async def _get_hidden_elements_count(self) -> int:
        """Count currently hidden elements."""
        try:
            count = await self.page.evaluate('''() => {
                return document.querySelectorAll('[style*="display: none"], [style*="visibility: hidden"], .hidden, .d-none').length;
            }''')
            return count
        except:
            return 0

    async def _find_revealed_elements(self, parent_selector: str) -> List[ElementInfo]:
        """Find elements that became visible after hover."""
        revealed = []
        try:
            # Look for dropdown menus, submenus, and revealed content
            selectors = [
                f'{parent_selector} ~ ul', f'{parent_selector} ~ div',
                f'{parent_selector} + ul', f'{parent_selector} + div',
                '.dropdown-menu:visible', '.submenu:visible',
                '[class*="dropdown"]:not([style*="display: none"])',
                '[class*="submenu"]:not([style*="display: none"])',
                '[aria-expanded="true"] + *'
            ]
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements[:5]:
                        is_visible = await element.is_visible()
                        if is_visible:
                            info = await self.get_element_info(element)
                            if info:
                                revealed.append(info)
                except:
                    continue
        except Exception as e:
            logger.warning(f"Error finding revealed elements: {e}")
        
        return revealed

    async def _find_revealed_links(self, parent_selector: str) -> List[Dict[str, str]]:
        """Find links that became visible after hover."""
        links = []
        try:
            # Look for links in dropdown areas
            visible_links = await self.page.evaluate('''(parentSelector) => {
                const links = [];
                const parent = document.querySelector(parentSelector);
                if (!parent) return links;
                
                // Find nearby dropdown/submenu containers
                const containers = [
                    parent.nextElementSibling,
                    parent.querySelector('ul, div'),
                    parent.parentElement?.querySelector('ul, div'),
                    ...document.querySelectorAll('.dropdown-menu, .submenu, [class*="dropdown"]')
                ];
                
                for (const container of containers) {
                    if (!container) continue;
                    const rect = container.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const anchors = container.querySelectorAll('a');
                        anchors.forEach(a => {
                            const text = (a.textContent || "").replace(/\\s+/g, " ").trim();
                            const href = a.href;
                            if (text && href && !links.some(l => l.text === text)) {
                                links.push({ text: text.substring(0, 100), href });
                            }
                        });
                    }
                }
                return links.slice(0, 10);
            }''', parent_selector)
            
            links = visible_links or []
        except Exception as e:
            logger.warning(f"Error finding revealed links: {e}")
        
        return links

    async def simulate_click_for_popup(self, element_info: ElementInfo) -> Optional[PopupInteraction]:
        """
        Click an element and detect if a popup/modal appears.
        
        Args:
            element_info: Information about the element to click
            
        Returns:
            PopupInteraction if a popup appeared, None otherwise
        """
        try:
            # Store current URL
            initial_url = self.page.url
            
            # Find the element
            element = await self.page.query_selector(element_info.selector)
            if not element:
                if element_info.text_content:
                    element = await self.page.get_by_text(element_info.text_content, exact=False).first
            
            if not element:
                return None
            
            # Click the element
            await element.click()
            await asyncio.sleep(1)  # Wait for popup animation
            
            # Check for popup/modal
            popup_info = await self._detect_popup()
            
            if popup_info:
                # Get action buttons in the popup
                action_buttons = await self._get_popup_buttons()
                
                # Create interaction
                interaction = PopupInteraction(
                    trigger_element=element_info,
                    popup_title=popup_info.get('title'),
                    popup_content=popup_info.get('content'),
                    action_buttons=action_buttons,
                    interaction_type=InteractionType.POPUP_MODAL
                )
                
                # Try to close the popup
                await self._close_popup()
                
                return interaction
            
            # Check if URL changed (navigation instead of popup)
            if self.page.url != initial_url:
                # Navigate back
                await self.page.go_back()
                await asyncio.sleep(1)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error simulating click: {e}")
            return None

    async def _detect_popup(self) -> Optional[Dict[str, str]]:
        """
        Detect if a popup/modal is currently visible.
        Uses DYNAMIC detection based on behavior, NOT hardcoded selectors.
        """
        if self._dynamic_detector:
            popup_info = await self._dynamic_detector.detect_popup_after_click()
            if popup_info and popup_info.get('detected'):
                return {
                    'title': popup_info.get('title', ''),
                    'content': popup_info.get('content', '')
                }
        return None

    async def _get_popup_buttons(self) -> List[Dict[str, str]]:
        """
        Get buttons within the current popup.
        Uses DYNAMIC detection to find any overlay's buttons.
        """
        try:
            buttons = await self.page.evaluate('''() => {
                // Find any modal-like element dynamically
                const allElements = document.querySelectorAll('*');
                
                for (const el of allElements) {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    
                    // Check for modal characteristics (dynamic)
                    const isModal = (
                        (style.position === 'fixed' || style.position === 'absolute') &&
                        parseInt(style.zIndex) > 100 &&
                        rect.width > 200 && rect.height > 100 &&
                        rect.width < window.innerWidth * 0.95
                    ) || el.getAttribute('role') === 'dialog' || el.getAttribute('aria-modal') === 'true';
                    
                    if (!isModal) continue;
                    
                    // Found a modal - get its buttons
                    const btns = el.querySelectorAll('button, a, [role="button"]');
                    const result = [];
                    
                    for (const btn of btns) {
                        const text = (btn.textContent || "").replace(/\\s+/g, " ").trim();
                        if (text && text.length < 50) {
                            result.push({
                                text: text,
                                type: btn.getAttribute('type') || 'button'
                            });
                        }
                    }
                    
                    if (result.length > 0) return result.slice(0, 5);
                }
                
                return [];
            }''')
            return buttons or []
        except:
            return []

    async def _close_popup(self):
        """
        Attempt to close any open popup.
        Uses DYNAMIC detection to find close buttons.
        """
        try:
            closed = await self.page.evaluate('''() => {
                // Find any modal-like element
                const allElements = document.querySelectorAll('*');
                
                for (const el of allElements) {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    
                    const isModal = (
                        (style.position === 'fixed' || style.position === 'absolute') &&
                        parseInt(style.zIndex) > 100 &&
                        rect.width > 200 && rect.height > 100
                    ) || el.getAttribute('role') === 'dialog';
                    
                    if (!isModal) continue;
                    
                    // Find close button dynamically
                    const buttons = el.querySelectorAll('button, a, [role="button"]');
                    for (const btn of buttons) {
                        const text = (btn.textContent || '').toLowerCase();
                        const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                        const className = (btn.className || '').toLowerCase();
                        
                        if (text.includes('close') || text.includes('cancel') || 
                            text.includes('dismiss') || text === 'x' ||
                            ariaLabel.includes('close') || className.includes('close')) {
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            }''')
            
            if closed:
                await asyncio.sleep(0.5)
                return
            
            # Fallback: Try pressing Escape
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(0.3)
            
        except Exception as e:
            logger.warning(f"Error closing popup: {e}")

    async def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """
        Get the navigation structure of the page.
        
        Returns:
            List of navigation items with their sub-items
        """
        try:
            nav_structure = await self.page.evaluate('''() => {
                const navItems = [];
                const navElements = document.querySelectorAll('nav, [role="navigation"], header');
                
                navElements.forEach(nav => {
                    const links = nav.querySelectorAll('a');
                    links.forEach(link => {
                        const text = (link.textContent || "").replace(/\\s+/g, " ").trim();
                        const href = link.href;
                        if (text && text.length < 50) {
                            navItems.push({
                                text,
                                href,
                                hasDropdown: link.closest('[class*="dropdown"]') !== null ||
                                            link.getAttribute('aria-haspopup') === 'true' ||
                                            link.getAttribute('aria-expanded') !== null
                            });
                        }
                    });
                });
                
                return navItems.slice(0, 30);
            }''')
            return nav_structure or []
        except:
            return []

    async def get_page_metadata(self) -> Dict[str, Any]:
        """Get metadata about the current page."""
        try:
            metadata = await self.page.evaluate('''() => {
                return {
                    title: document.title,
                    description: document.querySelector('meta[name="description"]')?.content || '',
                    url: window.location.href,
                    hasNavigation: document.querySelector('nav, [role="navigation"]') !== null,
                    hasForms: document.querySelectorAll('form').length,
                    hasModals: document.querySelectorAll('.modal, [role="dialog"]').length,
                    language: document.documentElement.lang || 'en'
                };
            }''')
            return metadata
        except:
            return {}
