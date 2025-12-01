"""
Gherkin Generator module.
Uses LLM (OpenAI GPT-4 or Google Gemini) to generate Gherkin scenarios.

Follows SOLID principles:
- SRP: Focuses only on Gherkin generation logic
- OCP: New LLM providers can be added without modifying this class
- DIP: Depends on ILLMProvider abstraction, not concrete implementations
"""

import os
import json
from typing import List, Dict, Any, Optional
import logging

from ..interfaces.llm import ILLMProvider, IGherkinGenerator
from ..models.schemas import (
    PageAnalysis, GherkinFeature, GherkinScenario,
    HoverInteraction, PopupInteraction
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import providers for backward compatibility
from .providers import OpenAIProvider, GeminiProvider


class GherkinGenerator(IGherkinGenerator):
    """
    Generates Gherkin scenarios from page analysis using LLM.
    
    Follows:
    - SRP: Only handles Gherkin generation, delegates LLM calls
    - OCP: Supports new LLM providers without code changes
    - DIP: Depends on ILLMProvider abstraction
    """

    def __init__(
        self, 
        llm_provider: Optional[ILLMProvider] = None,
        provider: str = "openai", 
        api_key: Optional[str] = None
    ):
        """
        Initialize the Gherkin generator.
        
        Args:
            llm_provider: Injected LLM provider (preferred for DIP)
            provider: LLM provider name ('openai' or 'gemini') - legacy
            api_key: API key for the provider - legacy
        """
        if llm_provider is not None:
            self.llm = llm_provider
        else:
            # Legacy initialization for backward compatibility
            self._init_legacy_provider(provider, api_key)
    
    def _init_legacy_provider(self, provider: str, api_key: Optional[str]) -> None:
        """Initialize LLM provider using legacy parameters."""
        provider_name = provider.lower()
        
        if api_key is None:
            if provider_name == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider_name == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                f"API key required for {provider}. "
                f"Set {provider.upper()}_API_KEY environment variable."
            )
        
        if provider_name == "openai":
            self.llm = OpenAIProvider(api_key=api_key)
        elif provider_name == "gemini":
            self.llm = GeminiProvider(api_key=api_key)
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. Use 'openai' or 'gemini'."
            )

    async def generate_features(self, analysis: PageAnalysis) -> List[GherkinFeature]:
        """
        Generate Gherkin features from page analysis.
        
        Args:
            analysis: PageAnalysis object with detected interactions
            
        Returns:
            List of GherkinFeature objects
        """
        features = []
        
        # Generate popup scenarios
        if analysis.popup_interactions:
            popup_feature = await self._generate_popup_feature(
                analysis.url, 
                analysis.popup_interactions
            )
            if popup_feature:
                features.append(popup_feature)
        
        # Generate hover scenarios
        if analysis.hover_interactions:
            hover_feature = await self._generate_hover_feature(
                analysis.url, 
                analysis.hover_interactions
            )
            if hover_feature:
                features.append(hover_feature)
        
        return features

    async def _generate_popup_feature(
        self, 
        url: str, 
        interactions: List[PopupInteraction]
    ) -> Optional[GherkinFeature]:
        """Generate feature for popup interactions."""
        
        # Prepare interaction data for the prompt
        interaction_data = []
        for interaction in interactions:
            data = {
                'trigger_text': interaction.trigger_element.text_content,
                'popup_title': interaction.popup_title,
                'popup_content': interaction.popup_content,
                'buttons': [b.get('text', '') for b in interaction.action_buttons],
                'redirect_url': interaction.redirect_url
            }
            interaction_data.append(data)
        
        prompt = f"""Generate Gherkin BDD test scenarios for popup/modal interactions on a webpage.

URL: {url}

Detected Popup Interactions:
{json.dumps(interaction_data, indent=2)}

Requirements:
1. Create a Feature for validating popup functionality
2. Generate Scenario(s) that test:
   - Opening the popup by clicking the trigger element
   - Verifying the popup title and content
   - Testing each button in the popup (cancel, continue, close, etc.)
   - Verifying URL changes after button clicks if applicable
3. Use proper Gherkin syntax with Given, When, Then, And steps
4. Make the scenarios descriptive and test real user flows
5. Include both positive and edge case scenarios where applicable

Output ONLY the Gherkin feature file content, starting with "Feature:" and nothing else.
Use proper indentation with 2 spaces.
"""

        try:
            gherkin_content = await self.llm.generate(prompt)
            return self._parse_gherkin_to_feature(gherkin_content, "popup")
        except Exception as e:
            logger.error(f"Error generating popup feature: {e}")
            return None

    async def _generate_hover_feature(
        self, 
        url: str, 
        interactions: List[HoverInteraction]
    ) -> Optional[GherkinFeature]:
        """Generate feature for hover interactions."""
        
        # Prepare interaction data for the prompt
        interaction_data = []
        for interaction in interactions:
            data = {
                'trigger_text': interaction.trigger_element.text_content,
                'revealed_links': interaction.revealed_links[:10],  # Limit
                'interaction_type': interaction.interaction_type.value
            }
            interaction_data.append(data)
        
        prompt = f"""Generate Gherkin BDD test scenarios for hover-based interactions on a webpage.

URL: {url}

Detected Hover Interactions:
{json.dumps(interaction_data, indent=2)}

Requirements:
1. Create a Feature for validating navigation menu/hover functionality
2. Generate Scenario(s) that test:
   - Hovering over menu items to reveal dropdowns
   - Verifying the dropdown content becomes visible
   - Clicking on revealed links
   - Verifying URL changes after clicking links
3. Use proper Gherkin syntax with Given, When, Then, And steps
4. Make the scenarios descriptive and test real user flows
5. Generate at least one scenario for each significant hover interaction

Output ONLY the Gherkin feature file content, starting with "Feature:" and nothing else.
Use proper indentation with 2 spaces.
"""

        try:
            gherkin_content = await self.llm.generate(prompt)
            return self._parse_gherkin_to_feature(gherkin_content, "hover")
        except Exception as e:
            logger.error(f"Error generating hover feature: {e}")
            return None

    def _parse_gherkin_to_feature(self, content: str, feature_type: str) -> GherkinFeature:
        """
        Parse Gherkin content string into GherkinFeature object.
        """
        lines = content.strip().split('\n')
        
        feature_name = ""
        feature_description = ""
        scenarios = []
        current_scenario = None
        current_steps = []
        tags = []
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('Feature:'):
                feature_name = stripped[8:].strip()
            elif stripped.startswith('@'):
                tags.extend([t.strip() for t in stripped.split() if t.startswith('@')])
            elif stripped.startswith('Scenario:') or stripped.startswith('Scenario Outline:'):
                # Save previous scenario
                if current_scenario and current_steps:
                    scenarios.append(GherkinScenario(
                        name=current_scenario,
                        steps=current_steps,
                        tags=tags.copy()
                    ))
                    tags = []
                
                current_scenario = stripped.split(':', 1)[1].strip()
                current_steps = []
            elif stripped.startswith(('Given', 'When', 'Then', 'And', 'But')):
                current_steps.append(stripped)
            elif stripped and not stripped.startswith('#') and current_scenario is None:
                # Feature description
                if feature_description:
                    feature_description += '\n'
                feature_description += stripped
        
        # Save last scenario
        if current_scenario and current_steps:
            scenarios.append(GherkinScenario(
                name=current_scenario,
                steps=current_steps,
                tags=tags
            ))
        
        return GherkinFeature(
            name=feature_name or f"{feature_type.title()} Interactions",
            description=feature_description or None,
            scenarios=scenarios,
            tags=[f"@{feature_type}"]
        )

    async def generate_combined_feature(self, analysis: PageAnalysis) -> str:
        """
        Generate a combined feature file content from all interactions.
        
        Args:
            analysis: PageAnalysis object
            
        Returns:
            Complete .feature file content as string
        """
        # Prepare comprehensive prompt
        popup_data = []
        for interaction in analysis.popup_interactions:
            popup_data.append({
                'trigger_text': interaction.trigger_element.text_content,
                'popup_title': interaction.popup_title,
                'popup_content': interaction.popup_content[:200] if interaction.popup_content else '',
                'buttons': [b.get('text', '') for b in interaction.action_buttons],
                'redirect_url': interaction.redirect_url
            })
        
        hover_data = []
        for interaction in analysis.hover_interactions:
            hover_data.append({
                'trigger_text': interaction.trigger_element.text_content,
                'revealed_links': interaction.revealed_links[:10]
            })
        
        prompt = f"""Generate comprehensive Gherkin BDD test scenarios for a webpage.

URL: {analysis.url}
Page Title: {analysis.page_title}

=== POPUP/MODAL INTERACTIONS ===
{json.dumps(popup_data, indent=2) if popup_data else "No popup interactions detected"}

=== HOVER/DROPDOWN INTERACTIONS ===
{json.dumps(hover_data, indent=2) if hover_data else "No hover interactions detected"}

=== REQUIREMENTS ===
1. Generate TWO Feature blocks:
   - Feature 1: Validate popup/modal functionality (if popup interactions exist)
   - Feature 2: Validate hover/navigation menu functionality (if hover interactions exist)

2. For POPUP scenarios, include:
   - Opening the popup by clicking the trigger
   - Verifying popup title appears
   - Testing Cancel button (popup closes, user stays on page)
   - Testing Continue/Confirm button (navigation to new URL)

3. For HOVER scenarios, include:
   - Hovering over navigation items
   - Verifying dropdown appears
   - Clicking revealed links
   - Verifying URL navigation

4. Use proper Gherkin syntax:
   - Given (precondition)
   - When (action)
   - Then (expected result)
   - And (additional steps)

5. Make scenarios descriptive and testable
6. Use actual element text and URLs from the data provided

Output ONLY valid Gherkin feature file content.
Separate multiple Features with a blank line.
Use 2-space indentation.
"""

        try:
            gherkin_content = await self.llm.generate(prompt)
            # Clean up the response
            gherkin_content = gherkin_content.strip()
            if gherkin_content.startswith('```'):
                # Remove markdown code blocks
                lines = gherkin_content.split('\n')
                lines = [l for l in lines if not l.startswith('```')]
                gherkin_content = '\n'.join(lines)
            return gherkin_content
        except Exception as e:
            logger.error(f"Error generating combined feature: {e}")
            return self._generate_fallback_feature(analysis)

    def _generate_fallback_feature(self, analysis: PageAnalysis) -> str:
        """Generate a basic feature file without LLM if there's an error."""
        feature_content = []
        
        if analysis.popup_interactions:
            feature_content.append("Feature: Validate popup functionality")
            feature_content.append("")
            
            for i, interaction in enumerate(analysis.popup_interactions[:3], 1):
                trigger = interaction.trigger_element.text_content or "element"
                title = interaction.popup_title or "popup"
                
                feature_content.append(f"  Scenario: Verify popup triggered by '{trigger}'")
                feature_content.append(f'    Given the user is on the "{analysis.url}" page')
                feature_content.append(f'    When the user clicks the "{trigger}" button')
                feature_content.append(f'    Then a popup should appear with the title "{title}"')
                
                for btn in interaction.action_buttons[:2]:
                    btn_text = btn.get('text', 'button')
                    feature_content.append(f'    When the user clicks the "{btn_text}" button')
                    feature_content.append(f'    Then the popup should close')
                
                feature_content.append("")
        
        if analysis.hover_interactions:
            feature_content.append("")
            feature_content.append("Feature: Validate navigation menu functionality")
            feature_content.append("")
            
            for i, interaction in enumerate(analysis.hover_interactions[:3], 1):
                trigger = interaction.trigger_element.text_content or "menu item"
                
                feature_content.append(f"  Scenario: Verify hover menu for '{trigger}'")
                feature_content.append(f'    Given the user is on the "{analysis.url}" page')
                feature_content.append(f'    When the user hovers over the navigation menu "{trigger}"')
                feature_content.append(f'    Then a dropdown should appear')
                
                if interaction.revealed_links:
                    link = interaction.revealed_links[0]
                    link_text = link.get('text', 'link')
                    link_href = link.get('href', '')
                    feature_content.append(f'    When the user clicks the link "{link_text}" from the dropdown')
                    if link_href:
                        feature_content.append(f'    Then the page URL should change to "{link_href}"')
                
                feature_content.append("")
        
        return '\n'.join(feature_content) if feature_content else "# No interactions detected"
