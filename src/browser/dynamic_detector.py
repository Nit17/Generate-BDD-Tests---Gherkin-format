"""
Dynamic Element Detector module.
Detects interactive elements through behavior analysis, not hardcoded selectors.

This module provides fully autonomous element detection by:
1. Analyzing computed styles for hover effects
2. Detecting visibility changes on interaction
3. Finding elements with event listeners
4. Analyzing DOM structure and relationships
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from playwright.async_api import Page, ElementHandle

from ..models.schemas import ElementInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _filter_none_values(d: Dict[str, Any]) -> Dict[str, str]:
    """Filter out None values from a dictionary and convert to strings."""
    return {k: str(v) for k, v in d.items() if v is not None}


class DynamicElementDetector:
    """
    Detects interactive elements dynamically through behavior analysis.
    No hardcoded selectors - analyzes page structure at runtime.
    """

    def __init__(self, page: Page):
        self.page = page
        self._interactive_cache: Dict[str, bool] = {}

    async def find_all_interactive_elements(self) -> List[ElementInfo]:
        """
        Find all potentially interactive elements on the page.
        Uses behavior analysis instead of hardcoded selectors.
        
        Returns:
            List of ElementInfo for interactive elements
        """
        logger.info("Dynamically detecting interactive elements...")
        
        # Get all visible, interactive elements
        interactive_elements = await self.page.evaluate('''() => {
            const results = [];
            const seen = new Set();
            
            // Get ALL elements on the page
            const allElements = document.querySelectorAll('*');
            
            for (const el of allElements) {
                // Skip non-visible elements
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                if (parseFloat(style.opacity) === 0) continue;
                
                // Check if element is interactive
                const isInteractive = (
                    // Naturally interactive elements
                    el.tagName === 'A' ||
                    el.tagName === 'BUTTON' ||
                    el.tagName === 'INPUT' ||
                    el.tagName === 'SELECT' ||
                    // Has click-related attributes
                    el.onclick !== null ||
                    el.hasAttribute('onclick') ||
                    el.hasAttribute('ng-click') ||
                    el.hasAttribute('@click') ||
                    el.hasAttribute('v-on:click') ||
                    // ARIA interactive roles
                    ['button', 'link', 'menuitem', 'tab', 'menuitemcheckbox', 'menuitemradio', 'option']
                        .includes(el.getAttribute('role')) ||
                    // Has tabindex (focusable)
                    el.hasAttribute('tabindex') ||
                    // Has data attributes suggesting interactivity
                    el.hasAttribute('data-toggle') ||
                    el.hasAttribute('data-bs-toggle') ||
                    el.hasAttribute('data-action') ||
                    el.hasAttribute('data-target') ||
                    el.hasAttribute('data-modal') ||
                    el.hasAttribute('data-popup') ||
                    // Has aria attributes suggesting interactivity
                    el.hasAttribute('aria-haspopup') ||
                    el.hasAttribute('aria-expanded') ||
                    el.hasAttribute('aria-controls') ||
                    // Cursor style indicates clickable
                    style.cursor === 'pointer'
                );
                
                if (!isInteractive) continue;
                
                // Get text content (normalized)
                const text = (el.textContent || '').replace(/\\s+/g, ' ').trim().substring(0, 200);
                
                // Skip if we've seen this text already (dedup)
                const textKey = text.toLowerCase().substring(0, 50);
                if (textKey && seen.has(textKey)) continue;
                if (textKey) seen.add(textKey);
                
                // Skip if no meaningful content
                if (!text && !el.getAttribute('aria-label') && !el.getAttribute('title')) continue;
                
                // Generate a unique selector
                let selector = '';
                if (el.id) {
                    selector = '#' + el.id;
                } else if (el.getAttribute('data-testid')) {
                    selector = `[data-testid="${el.getAttribute('data-testid')}"]`;
                } else if (el.getAttribute('aria-label')) {
                    selector = `[aria-label="${el.getAttribute('aria-label')}"]`;
                } else {
                    // Build path-based selector
                    const path = [];
                    let current = el;
                    while (current && current !== document.body && path.length < 3) {
                        let part = current.tagName.toLowerCase();
                        if (current.className && typeof current.className === 'string') {
                            const mainClass = current.className.split(' ').find(c => c && !c.includes(':'));
                            if (mainClass) part += '.' + mainClass.split(' ')[0];
                        }
                        path.unshift(part);
                        current = current.parentElement;
                    }
                    selector = path.join(' > ');
                }
                
                results.push({
                    selector,
                    tagName: el.tagName.toLowerCase(),
                    text,
                    ariaLabel: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    href: el.getAttribute('href'),
                    hasPopup: el.hasAttribute('aria-haspopup'),
                    isExpanded: el.getAttribute('aria-expanded'),
                    classes: (el.className || '').toString().split(' ').filter(c => c).slice(0, 5),
                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                });
                
                // Limit to prevent overwhelming
                if (results.length >= 100) break;
            }
            
            return results;
        }''')
        
        # Convert to ElementInfo objects
        elements = []
        for item in interactive_elements:
            elements.append(ElementInfo(
                selector=item['selector'],
                tag_name=item['tagName'],
                text_content=item['text'] or None,
                aria_label=item.get('ariaLabel'),
                role=item.get('role'),
                classes=item.get('classes', []),
                attributes=_filter_none_values({
                    'href': item.get('href'),
                    'has_popup': item.get('hasPopup', False),
                    'is_expanded': item.get('isExpanded')
                }),
                bounding_box=item.get('rect')
            ))
        
        logger.info(f"Found {len(elements)} interactive elements dynamically")
        return elements

    async def find_hoverable_elements(self) -> List[ElementInfo]:
        """
        Find elements that have hover effects or reveal content on hover.
        Detects by analyzing behavior, not by matching selectors.
        
        Returns:
            List of ElementInfo for elements with hover behavior
        """
        logger.info("Detecting elements with hover behavior...")
        
        # Get elements that might have hover effects
        hover_candidates = await self.page.evaluate('''() => {
            const results = [];
            const seen = new Set();
            
            // Get all visible anchor and button elements - expanded selectors for complex sites
            const elements = document.querySelectorAll(`
                a, button, [role="button"], [role="menuitem"], [role="tab"],
                li, [class*="nav"] > *, [class*="menu"] > *, [class*="gnb"] > *,
                nav > *, header a, header button, [data-nav], [data-menu]
            `.replace(/\\s+/g, ' '));
            
            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                if (rect.width < 10 || rect.height < 10) continue;
                
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                if (parseFloat(style.opacity) < 0.1) continue;
                
                const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                const textKey = text.toLowerCase().substring(0, 30);
                
                if (!text || text.length > 100 || seen.has(textKey)) continue;
                seen.add(textKey);
                
                // Check for hover-related indicators
                const hasHoverIndicators = (
                    // Has children or siblings that might be dropdowns
                    el.querySelector('ul, div, [class*="sub"], [class*="drop"], [class*="depth"]') !== null ||
                    el.nextElementSibling?.matches?.('ul, div, [class*="menu"], [class*="sub"]') ||
                    // Parent has dropdown-related structure
                    el.parentElement?.querySelector?.(':scope > ul, :scope > div, :scope > [class*="sub"]')?.children?.length > 0 ||
                    // ARIA indicators
                    el.hasAttribute('aria-haspopup') ||
                    el.hasAttribute('aria-expanded') ||
                    el.hasAttribute('aria-controls') ||
                    // Common hover patterns - in navigation context
                    el.closest('[class*="nav"], [class*="menu"], [class*="gnb"], nav, header') !== null ||
                    // Cursor pointer suggests interactivity
                    style.cursor === 'pointer'
                );
                
                // Generate selector
                let selector = '';
                if (el.id) {
                    selector = '#' + el.id;
                } else if (text && text.length <= 50) {
                    selector = `text="${text.substring(0, 50)}"`;
                } else {
                    const tagName = el.tagName.toLowerCase();
                    const cls = el.className?.split?.(' ')?.[0];
                    selector = cls ? `${tagName}.${cls}` : tagName;
                }
                
                results.push({
                    selector,
                    tagName: el.tagName.toLowerCase(),
                    text: text.substring(0, 200),
                    ariaLabel: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    href: el.getAttribute('href'),
                    hasHoverIndicators,
                    classes: (el.className || '').toString().split(' ').filter(c => c).slice(0, 5),
                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                });
                
                if (results.length >= 50) break;
            }
            
            // Sort by likelihood of having hover behavior
            return results.sort((a, b) => {
                if (a.hasHoverIndicators && !b.hasHoverIndicators) return -1;
                if (!a.hasHoverIndicators && b.hasHoverIndicators) return 1;
                return 0;
            });
        }''')
        
        elements = []
        for item in hover_candidates:
            # Only include href in attributes if it exists
            attrs = {}
            if item.get('href'):
                attrs['href'] = item['href']
            
            elements.append(ElementInfo(
                selector=item['selector'],
                tag_name=item['tagName'],
                text_content=item['text'] or None,
                aria_label=item.get('ariaLabel'),
                role=item.get('role'),
                classes=item.get('classes', []),
                attributes=attrs,
                bounding_box=item.get('rect')
            ))
        
        logger.info(f"Found {len(elements)} potential hover elements")
        return elements

    async def find_clickable_elements(self) -> List[ElementInfo]:
        """
        Find elements that might trigger popups, modals, or navigation on click.
        Detects by analyzing element behavior and attributes.
        
        Returns:
            List of ElementInfo for clickable elements
        """
        logger.info("Detecting clickable elements dynamically...")
        
        clickable = await self.page.evaluate('''() => {
            const results = [];
            const seen = new Set();
            
            // Get all potentially clickable elements
            const elements = document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"], [onclick], [tabindex]');
            
            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                
                const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                const textKey = text.toLowerCase().substring(0, 50);
                
                if (seen.has(textKey) && textKey) continue;
                if (textKey) seen.add(textKey);
                
                // Skip navigation links (regular hrefs)
                const href = el.getAttribute('href');
                if (href && href.startsWith('http') && !el.hasAttribute('target') && 
                    !el.hasAttribute('data-') && !el.hasAttribute('aria-haspopup')) {
                    continue;
                }
                
                // Check for popup/modal indicators
                const mightTriggerPopup = (
                    el.hasAttribute('data-modal') ||
                    el.hasAttribute('data-popup') ||
                    el.hasAttribute('data-toggle') ||
                    el.hasAttribute('data-bs-toggle') ||
                    el.hasAttribute('aria-haspopup') ||
                    el.getAttribute('target') === '_blank' ||
                    (href && href.startsWith('#')) ||
                    el.tagName === 'BUTTON' ||
                    style.cursor === 'pointer'
                );
                
                let selector = '';
                if (el.id) {
                    selector = '#' + el.id;
                } else if (text) {
                    selector = `text="${text.substring(0, 50)}"`;
                } else if (el.getAttribute('aria-label')) {
                    selector = `[aria-label="${el.getAttribute('aria-label')}"]`;
                } else {
                    selector = el.tagName.toLowerCase();
                }
                
                results.push({
                    selector,
                    tagName: el.tagName.toLowerCase(),
                    text: text.substring(0, 200),
                    ariaLabel: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    href,
                    mightTriggerPopup,
                    type: el.getAttribute('type'),
                    classes: (el.className || '').toString().split(' ').filter(c => c).slice(0, 5),
                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                });
                
                if (results.length >= 50) break;
            }
            
            // Sort by likelihood of triggering popup
            return results.sort((a, b) => {
                if (a.mightTriggerPopup && !b.mightTriggerPopup) return -1;
                if (!a.mightTriggerPopup && b.mightTriggerPopup) return 1;
                return 0;
            });
        }''')
        
        elements = []
        for item in clickable:
            elements.append(ElementInfo(
                selector=item['selector'],
                tag_name=item['tagName'],
                text_content=item['text'] or None,
                aria_label=item.get('ariaLabel'),
                role=item.get('role'),
                classes=item.get('classes', []),
                attributes=_filter_none_values({
                    'href': item.get('href'),
                    'type': item.get('type')
                }),
                bounding_box=item.get('rect')
            ))
        
        logger.info(f"Found {len(elements)} clickable elements")
        return elements

    async def detect_hover_effect(self, element: ElementInfo) -> Dict[str, Any]:
        """
        Detect if an element has a hover effect by actually hovering over it.
        Compares DOM state before and after hover.
        
        Args:
            element: Element to test for hover effects
            
        Returns:
            Dict with detected hover effects
        """
        try:
            # Get DOM state before hover
            before_state = await self._get_dom_snapshot()
            
            # Find and hover the element
            el = await self.page.query_selector(element.selector)
            if not el:
                # Try text selector
                if element.text_content:
                    el = await self.page.query_selector(f'text="{element.text_content[:50]}"')
            
            if not el:
                return {'has_effect': False, 'reason': 'element_not_found'}
            
            # Hover over element
            await el.hover()
            await asyncio.sleep(0.5)  # Wait for animations
            
            # Get DOM state after hover
            after_state = await self._get_dom_snapshot()
            
            # Compare states
            changes = self._compare_dom_states(before_state, after_state)
            
            return {
                'has_effect': changes['has_changes'],
                'new_elements': changes['new_elements'],
                'visibility_changes': changes['visibility_changes'],
                'revealed_links': changes.get('revealed_links', [])
            }
            
        except Exception as e:
            logger.warning(f"Error detecting hover effect: {e}")
            return {'has_effect': False, 'reason': str(e)}

    async def _get_dom_snapshot(self) -> Dict[str, Any]:
        """Get current DOM state for comparison."""
        return await self.page.evaluate('''() => {
            const visibleElements = new Set();
            const allElements = document.querySelectorAll('*');
            
            for (const el of allElements) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                
                if (rect.width > 0 && rect.height > 0 && 
                    style.display !== 'none' && 
                    style.visibility !== 'hidden' &&
                    parseFloat(style.opacity) > 0) {
                    
                    // Create a unique identifier for this element
                    const id = el.id || el.className || el.tagName;
                    const text = (el.textContent || '').substring(0, 50);
                    visibleElements.add(`${id}:${text}`);
                }
            }
            
            // Get visible links
            const links = [];
            document.querySelectorAll('a:not([style*="display: none"])').forEach(a => {
                const rect = a.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    const text = (a.textContent || '').replace(/\\s+/g, ' ').trim();
                    if (text) {
                        links.push({ text: text.substring(0, 100), href: a.href });
                    }
                }
            });
            
            return {
                visibleCount: visibleElements.size,
                visibleElements: Array.from(visibleElements),
                links
            };
        }''')

    def _compare_dom_states(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """Compare two DOM snapshots to detect changes."""
        before_set = set(before.get('visibleElements', []))
        after_set = set(after.get('visibleElements', []))
        
        new_elements = list(after_set - before_set)
        removed_elements = list(before_set - after_set)
        
        # Find new links
        before_links = {l['text'] for l in before.get('links', [])}
        after_links = after.get('links', [])
        new_links = [l for l in after_links if l['text'] not in before_links]
        
        return {
            'has_changes': len(new_elements) > 0 or len(new_links) > 0,
            'new_elements': new_elements[:10],
            'removed_elements': removed_elements[:10],
            'visibility_changes': len(new_elements) + len(removed_elements),
            'revealed_links': new_links[:10]
        }

    async def detect_popup_after_click(self) -> Optional[Dict[str, Any]]:
        """
        Detect if a popup/modal appeared after a click action.
        Uses behavior detection, not hardcoded selectors.
        
        Returns:
            Dict with popup info if detected, None otherwise
        """
        return await self.page.evaluate('''() => {
            // Find any element that looks like a popup/modal
            const allElements = document.querySelectorAll('*');
            
            for (const el of allElements) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                
                // Skip if not visible
                if (rect.width < 100 || rect.height < 50) continue;
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                if (parseFloat(style.opacity) === 0) continue;
                
                // Check for modal-like characteristics
                const isModal = (
                    // Fixed or absolute positioning (overlays)
                    (style.position === 'fixed' || style.position === 'absolute') &&
                    // Has significant z-index
                    parseInt(style.zIndex) > 100 &&
                    // Reasonable size for a modal
                    rect.width > 200 && rect.height > 100 &&
                    // Not full page (probably not a regular section)
                    rect.width < window.innerWidth * 0.95
                ) || (
                    // ARIA dialog
                    el.getAttribute('role') === 'dialog' ||
                    el.getAttribute('aria-modal') === 'true'
                );
                
                if (isModal) {
                    // Find title
                    const titleEl = el.querySelector('h1, h2, h3, [class*="title"], [class*="header"]');
                    const title = titleEl ? 
                        (titleEl.textContent || '').replace(/\\s+/g, ' ').trim().substring(0, 200) : '';
                    
                    // Find content
                    const contentEl = el.querySelector('p, [class*="content"], [class*="body"]');
                    const content = contentEl ? 
                        (contentEl.textContent || '').replace(/\\s+/g, ' ').trim().substring(0, 500) : '';
                    
                    // Find buttons
                    const buttons = [];
                    el.querySelectorAll('button, a[role="button"], [class*="btn"]').forEach(btn => {
                        const text = (btn.textContent || '').replace(/\\s+/g, ' ').trim();
                        if (text && text.length < 50) {
                            buttons.push({ text, type: btn.getAttribute('type') || 'button' });
                        }
                    });
                    
                    return {
                        detected: true,
                        title,
                        content,
                        buttons: buttons.slice(0, 5),
                        position: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                    };
                }
            }
            
            return { detected: false };
        }''')

    async def dismiss_overlays(self) -> bool:
        """
        Dynamically detect and dismiss any overlay (cookie banners, popups, etc.)
        Uses behavior detection, not hardcoded selectors.
        
        Returns:
            True if an overlay was dismissed
        """
        dismissed = await self.page.evaluate('''() => {
            // Find overlay-like elements
            const allElements = document.querySelectorAll('*');
            
            for (const el of allElements) {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                // Check for overlay characteristics
                const isOverlay = (
                    style.position === 'fixed' &&
                    parseInt(style.zIndex) > 1000 &&
                    rect.width > 100 &&
                    rect.height > 50
                );
                
                if (!isOverlay) continue;
                
                // Look for accept/close/dismiss buttons
                const buttons = el.querySelectorAll('button, a, [role="button"]');
                for (const btn of buttons) {
                    const text = (btn.textContent || '').toLowerCase();
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                    
                    // Check for accept/close patterns
                    if (text.includes('accept') || text.includes('agree') || 
                        text.includes('ok') || text.includes('close') ||
                        text.includes('dismiss') || text.includes('got it') ||
                        text.includes('i understand') || text.includes('continue') ||
                        ariaLabel.includes('close') || ariaLabel.includes('accept')) {
                        
                        btn.click();
                        return true;
                    }
                }
                
                // Try X button or close icon
                const closeBtn = el.querySelector('[aria-label*="close" i], [aria-label*="dismiss" i], .close, [class*="close"]');
                if (closeBtn) {
                    closeBtn.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if dismissed:
            await asyncio.sleep(0.5)  # Wait for animation
            logger.info("Dismissed an overlay dynamically")
        
        return dismissed

    async def get_page_structure(self) -> Dict[str, Any]:
        """
        Analyze the page structure dynamically to understand layout.
        
        Returns:
            Dict with page structure information
        """
        return await self.page.evaluate('''() => {
            const structure = {
                hasNavigation: false,
                hasHeader: false,
                hasFooter: false,
                hasSidebar: false,
                hasMain: false,
                navigationItems: [],
                interactiveRegions: []
            };
            
            // Detect semantic regions
            structure.hasNavigation = document.querySelector('nav, [role="navigation"]') !== null;
            structure.hasHeader = document.querySelector('header, [role="banner"]') !== null;
            structure.hasFooter = document.querySelector('footer, [role="contentinfo"]') !== null;
            structure.hasSidebar = document.querySelector('aside, [role="complementary"]') !== null;
            structure.hasMain = document.querySelector('main, [role="main"]') !== null;
            
            // Get navigation items
            const navElements = document.querySelectorAll('nav a, [role="navigation"] a, header a');
            navElements.forEach(a => {
                const text = (a.textContent || '').replace(/\\s+/g, ' ').trim();
                if (text && text.length < 50) {
                    structure.navigationItems.push({
                        text,
                        href: a.href,
                        hasSubmenu: a.closest('[class*="dropdown"], [class*="menu"]')?.querySelector('ul, [class*="sub"]') !== null
                    });
                }
            });
            
            // Limit
            structure.navigationItems = structure.navigationItems.slice(0, 30);
            
            return structure;
        }''')
