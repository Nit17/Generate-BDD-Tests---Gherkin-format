"""
Browser automation module using Playwright.
Handles page loading, element interaction, and state capture.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, ElementHandle, Locator
import logging

from ..models.schemas import ElementInfo, HoverInteraction, PopupInteraction, InteractionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserAutomation:
    """
    Playwright-based browser automation for detecting and interacting with web elements.
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the browser automation.
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-web-security', '--disable-features=IsolateOrigins,site-per-process']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await context.new_page()
        self.page.set_default_timeout(self.timeout)

    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL and wait for the page to load.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Page metadata including title and URL
        """
        logger.info(f"Navigating to: {url}")
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(2)  # Additional wait for dynamic content
        
        title = await self.page.title()
        current_url = self.page.url
        
        return {
            'title': title,
            'url': current_url,
            'loaded': True
        }

    async def get_element_info(self, element: ElementHandle) -> Optional[ElementInfo]:
        """
        Extract information from an element handle.
        
        Args:
            element: Playwright ElementHandle
            
        Returns:
            ElementInfo object with element details
        """
        try:
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            text_content = await element.evaluate('el => el.textContent?.trim()?.substring(0, 200) || ""')
            aria_label = await element.get_attribute('aria-label')
            role = await element.get_attribute('role')
            class_attr = await element.get_attribute('class') or ''
            classes = class_attr.split() if class_attr else []
            
            # Get relevant attributes
            attributes = {}
            for attr in ['href', 'data-testid', 'id', 'name', 'type', 'title']:
                value = await element.get_attribute(attr)
                if value:
                    attributes[attr] = value

            # Try to get bounding box
            bounding_box = None
            try:
                box = await element.bounding_box()
                if box:
                    bounding_box = box
            except:
                pass

            # Generate a selector
            selector = await self._generate_selector(element)

            return ElementInfo(
                selector=selector,
                tag_name=tag_name,
                text_content=text_content[:200] if text_content else None,
                aria_label=aria_label,
                role=role,
                classes=classes[:10],  # Limit classes
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
                if (el.getAttribute('data-testid')) return `[data-testid="${el.getAttribute('data-testid')}"]`;
                
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

    async def find_hoverable_elements(self) -> List[ElementInfo]:
        """
        Find elements that are likely to have hover interactions.
        
        Returns:
            List of ElementInfo for hoverable elements
        """
        logger.info("Finding hoverable elements...")
        
        # Find navigation elements, buttons, and elements with hover-related attributes
        selectors = [
            'nav a', 'nav button', 'nav li',
            'header a', 'header button',
            '[class*="nav"] a', '[class*="menu"] a', '[class*="dropdown"]',
            '[role="navigation"] a', '[role="menuitem"]',
            'a[class*="hover"]', '[class*="tooltip"]',
            '[aria-haspopup="true"]', '[aria-expanded]',
            '.nav-item', '.menu-item', '.dropdown-toggle',
            '[data-toggle="dropdown"]', '[data-bs-toggle="dropdown"]'
        ]
        
        hoverable_elements = []
        seen_texts = set()
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements[:20]:  # Limit per selector
                    try:
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue
                        
                        info = await self.get_element_info(element)
                        if info and info.text_content:
                            # Deduplicate by text content
                            text_key = info.text_content.strip().lower()[:50]
                            if text_key and text_key not in seen_texts:
                                seen_texts.add(text_key)
                                hoverable_elements.append(info)
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        logger.info(f"Found {len(hoverable_elements)} potential hoverable elements")
        return hoverable_elements

    async def find_clickable_buttons(self) -> List[ElementInfo]:
        """
        Find buttons that might trigger popups or modals.
        
        Returns:
            List of ElementInfo for clickable buttons
        """
        logger.info("Finding clickable buttons...")
        
        selectors = [
            'button', 'a.btn', 'a.button', '.btn', '.button',
            '[role="button"]', 'input[type="button"]', 'input[type="submit"]',
            '[class*="cta"]', '[class*="learn-more"]', '[class*="read-more"]',
            'a[target="_blank"]', '[data-modal]', '[data-popup]',
            '[class*="modal-trigger"]', '[class*="popup-trigger"]'
        ]
        
        buttons = []
        seen_texts = set()
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements[:15]:
                    try:
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue
                        
                        info = await self.get_element_info(element)
                        if info and info.text_content:
                            text_key = info.text_content.strip().lower()[:50]
                            if text_key and text_key not in seen_texts and len(text_key) > 2:
                                seen_texts.add(text_key)
                                buttons.append(info)
                    except:
                        continue
            except:
                continue
        
        logger.info(f"Found {len(buttons)} potential clickable buttons")
        return buttons

    async def simulate_hover(self, element_info: ElementInfo) -> Optional[HoverInteraction]:
        """
        Simulate hovering over an element and detect what appears.
        
        Args:
            element_info: Information about the element to hover
            
        Returns:
            HoverInteraction with revealed elements, or None if nothing appeared
        """
        try:
            # Get initial state of hidden elements
            initial_hidden = await self._get_hidden_elements_count()
            
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
            await asyncio.sleep(0.5)  # Wait for animations
            
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
                            const text = a.textContent?.trim();
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
        """Detect if a popup/modal is currently visible."""
        try:
            popup_info = await self.page.evaluate('''() => {
                // Common popup/modal selectors
                const selectors = [
                    '.modal:not([style*="display: none"])',
                    '.popup:not([style*="display: none"])',
                    '[role="dialog"]:not([style*="display: none"])',
                    '.overlay:not([style*="display: none"])',
                    '[class*="modal"]:not([style*="display: none"])',
                    '[class*="popup"]:not([style*="display: none"])',
                    '[class*="dialog"]:not([style*="display: none"])',
                    '.ReactModal__Content',
                    '[aria-modal="true"]'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 100 && rect.height > 50) {
                            // Found a visible popup
                            const title = el.querySelector('h1, h2, h3, .modal-title, .popup-title, [class*="title"]');
                            const content = el.querySelector('.modal-body, .popup-content, p');
                            return {
                                title: title?.textContent?.trim()?.substring(0, 200) || '',
                                content: content?.textContent?.trim()?.substring(0, 500) || ''
                            };
                        }
                    }
                }
                return null;
            }''')
            return popup_info
        except:
            return None

    async def _get_popup_buttons(self) -> List[Dict[str, str]]:
        """Get buttons within the current popup."""
        try:
            buttons = await self.page.evaluate('''() => {
                const popup = document.querySelector('.modal, .popup, [role="dialog"], [class*="modal"], [aria-modal="true"]');
                if (!popup) return [];
                
                const btns = popup.querySelectorAll('button, a.btn, .btn, [role="button"]');
                return Array.from(btns).map(btn => ({
                    text: btn.textContent?.trim()?.substring(0, 50) || '',
                    type: btn.getAttribute('type') || 'button'
                })).filter(b => b.text).slice(0, 5);
            }''')
            return buttons or []
        except:
            return []

    async def _close_popup(self):
        """Attempt to close any open popup."""
        try:
            # Try common close button selectors
            close_selectors = [
                '.modal .close', '.popup .close', '[aria-label="Close"]',
                '.modal-close', '.popup-close', 'button.close',
                '[class*="close"]', '.dismiss', '.cancel'
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = await self.page.query_selector(selector)
                    if close_btn and await close_btn.is_visible():
                        await close_btn.click()
                        await asyncio.sleep(0.5)
                        return
                except:
                    continue
            
            # Try pressing Escape
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
                        const text = link.textContent?.trim();
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
