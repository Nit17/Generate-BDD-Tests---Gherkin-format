"""Pydantic models for data schemas."""

import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


def clean_whitespace(text: Optional[str]) -> Optional[str]:
    """Normalize whitespace in text: replace multiple spaces/newlines with single space."""
    if text is None:
        return None
    return re.sub(r'\s+', ' ', text).strip() or None


class InteractionType(str, Enum):
    """Types of interactions detected on a webpage."""
    HOVER_DROPDOWN = "hover_dropdown"
    POPUP_MODAL = "popup_modal"
    TOOLTIP = "tooltip"
    IMAGE_OVERLAY = "image_overlay"
    ACCORDION = "accordion"
    CLICK_REVEAL = "click_reveal"


class ElementInfo(BaseModel):
    """Information about a detected element."""
    selector: str = Field(..., description="CSS selector for the element")
    tag_name: str = Field(..., description="HTML tag name")
    text_content: Optional[str] = Field(None, description="Text content of the element")
    aria_label: Optional[str] = Field(None, description="ARIA label if present")
    role: Optional[str] = Field(None, description="ARIA role if present")
    classes: List[str] = Field(default_factory=list, description="CSS classes")
    attributes: Dict[str, str] = Field(default_factory=dict, description="Relevant attributes")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Element position and size")

    @field_validator('text_content', mode='before')
    @classmethod
    def normalize_text_content(cls, v):
        """Clean whitespace from text content."""
        return clean_whitespace(v)


class HoverInteraction(BaseModel):
    """Represents a hover interaction and its result."""
    trigger_element: ElementInfo = Field(..., description="Element that triggers the hover")
    revealed_elements: List[ElementInfo] = Field(default_factory=list, description="Elements revealed on hover")
    revealed_links: List[Dict[str, str]] = Field(default_factory=list, description="Links revealed with text and href")
    interaction_type: InteractionType = Field(default=InteractionType.HOVER_DROPDOWN)


class PopupInteraction(BaseModel):
    """Represents a popup/modal interaction."""
    trigger_element: ElementInfo = Field(..., description="Element that triggers the popup")
    popup_title: Optional[str] = Field(None, description="Title of the popup")
    popup_content: Optional[str] = Field(None, description="Main content of the popup")
    action_buttons: List[Dict[str, str]] = Field(default_factory=list, description="Buttons in the popup")
    close_button: Optional[ElementInfo] = Field(None, description="Close button if present")
    redirect_url: Optional[str] = Field(None, description="URL redirected to after action")
    interaction_type: InteractionType = Field(default=InteractionType.POPUP_MODAL)

    @field_validator('popup_title', 'popup_content', mode='before')
    @classmethod
    def normalize_popup_text(cls, v):
        """Clean whitespace from popup text."""
        return clean_whitespace(v)


class PageAnalysis(BaseModel):
    """Complete analysis of a webpage."""
    url: str = Field(..., description="The analyzed URL")
    page_title: str = Field(..., description="Page title")
    hover_interactions: List[HoverInteraction] = Field(default_factory=list)
    popup_interactions: List[PopupInteraction] = Field(default_factory=list)
    navigation_elements: List[ElementInfo] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GherkinScenario(BaseModel):
    """A single Gherkin scenario."""
    name: str = Field(..., description="Scenario name")
    steps: List[str] = Field(..., description="Gherkin steps")
    tags: List[str] = Field(default_factory=list, description="Scenario tags")


class GherkinFeature(BaseModel):
    """A complete Gherkin feature."""
    name: str = Field(..., description="Feature name")
    description: Optional[str] = Field(None, description="Feature description")
    scenarios: List[GherkinScenario] = Field(..., description="List of scenarios")
    tags: List[str] = Field(default_factory=list, description="Feature tags")


class GenerationRequest(BaseModel):
    """Request model for test generation."""
    url: str = Field(..., description="URL to analyze")
    include_hover: bool = Field(default=True, description="Include hover interactions")
    include_popups: bool = Field(default=True, description="Include popup interactions")
    max_scenarios: int = Field(default=10, description="Maximum scenarios to generate")


class GenerationResponse(BaseModel):
    """Response model for test generation."""
    url: str
    features: List[GherkinFeature]
    feature_content: str = Field(..., description="Complete .feature file content")
    analysis_summary: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
