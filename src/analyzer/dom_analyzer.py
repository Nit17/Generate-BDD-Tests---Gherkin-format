"""
DOM Analyzer module for analyzing webpage structure.
Uses BeautifulSoup and lxml for HTML parsing.
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging

from ..models.schemas import ElementInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DOMAnalyzer:
    """
    Analyzes DOM structure to identify interactive elements.
    """

    def __init__(self, html_content: str):
        """
        Initialize the DOM analyzer.
        
        Args:
            html_content: Raw HTML content of the page
        """
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.html_content = html_content

    def find_navigation_menus(self) -> List[Dict[str, Any]]:
        """
        Find navigation menus in the page.
        
        Returns:
            List of navigation menu information
        """
        nav_menus = []
        
        # Find nav elements
        nav_elements = self.soup.find_all(['nav', 'header'])
        nav_elements.extend(self.soup.find_all(role='navigation'))
        nav_elements.extend(self.soup.find_all(class_=lambda x: x and ('nav' in x.lower() or 'menu' in x.lower())))
        
        for nav in nav_elements[:10]:  # Limit to prevent too many
            menu_items = []
            links = nav.find_all('a', limit=20)
            
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                
                # Check if it has dropdown indicators
                has_dropdown = (
                    link.get('aria-haspopup') == 'true' or
                    link.get('aria-expanded') is not None or
                    link.find_parent(class_=lambda x: x and 'dropdown' in x.lower()) is not None or
                    link.find(['ul', 'div'], class_=lambda x: x and ('dropdown' in x.lower() or 'submenu' in x.lower()))
                )
                
                if text and len(text) < 50:
                    menu_items.append({
                        'text': text,
                        'href': href,
                        'has_dropdown': has_dropdown,
                        'classes': link.get('class', [])
                    })
            
            if menu_items:
                nav_menus.append({
                    'type': nav.name,
                    'items': menu_items,
                    'classes': nav.get('class', [])
                })
        
        return nav_menus

    def find_interactive_elements(self) -> List[Dict[str, Any]]:
        """
        Find elements that are likely interactive (buttons, links, etc).
        
        Returns:
            List of interactive element information
        """
        interactive = []
        
        # Find buttons
        buttons = self.soup.find_all(['button', 'input'])
        buttons.extend(self.soup.find_all(role='button'))
        buttons.extend(self.soup.find_all(class_=lambda x: x and ('btn' in x.lower() or 'button' in x.lower())))
        
        for btn in buttons[:30]:
            text = btn.get_text(strip=True) or btn.get('value', '') or btn.get('aria-label', '')
            if text and len(text) < 100:
                interactive.append({
                    'type': 'button',
                    'text': text,
                    'id': btn.get('id'),
                    'classes': btn.get('class', []),
                    'aria_label': btn.get('aria-label'),
                    'data_attrs': {k: v for k, v in btn.attrs.items() if k.startswith('data-')}
                })
        
        # Find links that might trigger actions
        action_links = self.soup.find_all('a', href=lambda x: x and (
            x.startswith('#') or 
            x.startswith('javascript:') or
            'modal' in x.lower() or
            'popup' in x.lower()
        ))
        action_links.extend(self.soup.find_all('a', target='_blank'))
        action_links.extend(self.soup.find_all('a', class_=lambda x: x and (
            'learn' in ' '.join(x).lower() or 
            'more' in ' '.join(x).lower() or
            'cta' in ' '.join(x).lower()
        )))
        
        for link in action_links[:20]:
            text = link.get_text(strip=True)
            if text and len(text) < 100:
                interactive.append({
                    'type': 'link',
                    'text': text,
                    'href': link.get('href', ''),
                    'target': link.get('target'),
                    'classes': link.get('class', [])
                })
        
        return interactive

    def find_dropdown_containers(self) -> List[Dict[str, Any]]:
        """
        Find dropdown/submenu containers.
        
        Returns:
            List of dropdown container information
        """
        dropdowns = []
        
        dropdown_selectors = [
            lambda x: x and 'dropdown' in x.lower(),
            lambda x: x and 'submenu' in x.lower(),
            lambda x: x and 'mega-menu' in x.lower()
        ]
        
        for selector in dropdown_selectors:
            elements = self.soup.find_all(class_=selector)
            for el in elements[:10]:
                # Find the trigger and content
                trigger = el.find(['a', 'button', 'span'], class_=lambda x: x and 'toggle' in ' '.join(x or []).lower())
                if not trigger:
                    trigger = el.find(['a', 'button'])
                
                content = el.find(['ul', 'div'], class_=lambda x: x and ('menu' in ' '.join(x or []).lower() or 'content' in ' '.join(x or []).lower()))
                if not content:
                    content = el.find(['ul', 'div'])
                
                if trigger:
                    trigger_text = trigger.get_text(strip=True)
                    items = []
                    if content:
                        for item in content.find_all('a', limit=10):
                            item_text = item.get_text(strip=True)
                            if item_text:
                                items.append({
                                    'text': item_text,
                                    'href': item.get('href', '')
                                })
                    
                    if trigger_text:
                        dropdowns.append({
                            'trigger_text': trigger_text,
                            'items': items,
                            'classes': el.get('class', [])
                        })
        
        return dropdowns

    def find_modal_triggers(self) -> List[Dict[str, Any]]:
        """
        Find elements that might trigger modals/popups.
        
        Returns:
            List of modal trigger information
        """
        triggers = []
        
        # Elements with modal-related attributes
        modal_attrs = ['data-modal', 'data-popup', 'data-toggle', 'data-bs-toggle', 'data-target', 'data-bs-target']
        
        for attr in modal_attrs:
            elements = self.soup.find_all(attrs={attr: True})
            for el in elements[:10]:
                text = el.get_text(strip=True)
                if text:
                    triggers.append({
                        'text': text,
                        'trigger_attr': attr,
                        'trigger_value': el.get(attr),
                        'target': el.get('data-target') or el.get('data-bs-target'),
                        'tag': el.name
                    })
        
        # Links to external sites (often have leaving warnings)
        external_links = self.soup.find_all('a', target='_blank')
        for link in external_links[:10]:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if text and href and not href.startswith('#'):
                triggers.append({
                    'text': text,
                    'href': href,
                    'type': 'external_link',
                    'tag': 'a'
                })
        
        return triggers

    def find_tooltip_elements(self) -> List[Dict[str, Any]]:
        """
        Find elements that have tooltips.
        
        Returns:
            List of tooltip element information
        """
        tooltips = []
        
        # Elements with title attribute
        title_elements = self.soup.find_all(attrs={'title': True})
        for el in title_elements[:15]:
            text = el.get_text(strip=True)
            title = el.get('title')
            if title:
                tooltips.append({
                    'element_text': text[:50] if text else '',
                    'tooltip_text': title,
                    'tag': el.name
                })
        
        # Elements with tooltip classes
        tooltip_elements = self.soup.find_all(class_=lambda x: x and 'tooltip' in ' '.join(x or []).lower())
        for el in tooltip_elements[:10]:
            text = el.get_text(strip=True)
            if text:
                tooltips.append({
                    'element_text': text[:100],
                    'type': 'css_tooltip',
                    'tag': el.name
                })
        
        return tooltips

    def get_page_structure_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the page structure.
        
        Returns:
            Dictionary with page structure summary
        """
        return {
            'title': self.soup.title.string if self.soup.title else '',
            'has_navigation': len(self.soup.find_all(['nav', 'header'])) > 0,
            'navigation_count': len(self.find_navigation_menus()),
            'interactive_elements': len(self.find_interactive_elements()),
            'dropdown_count': len(self.find_dropdown_containers()),
            'modal_triggers': len(self.find_modal_triggers()),
            'tooltip_elements': len(self.find_tooltip_elements()),
            'forms_count': len(self.soup.find_all('form')),
            'images_count': len(self.soup.find_all('img')),
            'links_count': len(self.soup.find_all('a'))
        }

    def extract_all_interactions(self) -> Dict[str, Any]:
        """
        Extract all interactive elements and their relationships.
        
        Returns:
            Complete interaction map of the page
        """
        return {
            'navigation_menus': self.find_navigation_menus(),
            'interactive_elements': self.find_interactive_elements(),
            'dropdowns': self.find_dropdown_containers(),
            'modal_triggers': self.find_modal_triggers(),
            'tooltips': self.find_tooltip_elements(),
            'summary': self.get_page_structure_summary()
        }
