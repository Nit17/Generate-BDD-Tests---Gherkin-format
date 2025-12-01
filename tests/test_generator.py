"""
Tests for the BDD Test Generator.
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzer.dom_analyzer import DOMAnalyzer
from src.models.schemas import (
    ElementInfo, HoverInteraction, PopupInteraction,
    PageAnalysis, GherkinFeature, GherkinScenario
)
from src.output.feature_writer import FeatureWriter


class TestDOMAnalyzer:
    """Tests for DOM Analyzer."""
    
    def test_find_navigation_menus(self):
        """Test navigation menu detection."""
        html = """
        <html>
            <nav>
                <a href="/home">Home</a>
                <a href="/about" aria-haspopup="true">About</a>
                <a href="/contact">Contact</a>
            </nav>
        </html>
        """
        analyzer = DOMAnalyzer(html)
        menus = analyzer.find_navigation_menus()
        
        assert len(menus) > 0
        assert any('About' in str(menu) for menu in menus)
    
    def test_find_interactive_elements(self):
        """Test interactive element detection."""
        html = """
        <html>
            <button>Click Me</button>
            <a href="#" class="btn">Learn More</a>
            <input type="submit" value="Submit">
        </html>
        """
        analyzer = DOMAnalyzer(html)
        elements = analyzer.find_interactive_elements()
        
        assert len(elements) >= 2
    
    def test_find_modal_triggers(self):
        """Test modal trigger detection."""
        html = """
        <html>
            <button data-toggle="modal" data-target="#myModal">Open Modal</button>
            <a href="https://external.com" target="_blank">External Link</a>
        </html>
        """
        analyzer = DOMAnalyzer(html)
        triggers = analyzer.find_modal_triggers()
        
        assert len(triggers) >= 1
    
    def test_page_structure_summary(self):
        """Test page structure summary."""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <nav><a href="/">Home</a></nav>
                <form><input type="text"></form>
                <a href="/link">Link</a>
            </body>
        </html>
        """
        analyzer = DOMAnalyzer(html)
        summary = analyzer.get_page_structure_summary()
        
        assert summary['title'] == 'Test Page'
        assert summary['has_navigation'] == True
        assert summary['forms_count'] == 1


class TestFeatureWriter:
    """Tests for Feature Writer."""
    
    def test_format_feature(self, tmp_path):
        """Test feature formatting."""
        writer = FeatureWriter(output_dir=str(tmp_path))
        
        feature = GherkinFeature(
            name="Test Feature",
            description="This is a test",
            scenarios=[
                GherkinScenario(
                    name="Test Scenario",
                    steps=[
                        "Given the user is on the home page",
                        "When the user clicks the button",
                        "Then something happens"
                    ]
                )
            ]
        )
        
        content = writer._format_feature(feature)
        
        assert "Feature: Test Feature" in content
        assert "Scenario: Test Scenario" in content
        assert "Given the user is on the home page" in content
    
    def test_write_feature(self, tmp_path):
        """Test writing feature file."""
        writer = FeatureWriter(output_dir=str(tmp_path))
        
        feature = GherkinFeature(
            name="Test Feature",
            scenarios=[
                GherkinScenario(
                    name="Test Scenario",
                    steps=["Given I am testing", "Then it works"]
                )
            ]
        )
        
        path = writer.write_feature(feature, "test_feature")
        
        assert os.path.exists(path)
        assert path.endswith(".feature")
        
        with open(path, 'r') as f:
            content = f.read()
        
        assert "Feature: Test Feature" in content
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        writer = FeatureWriter()
        
        assert writer._sanitize_filename("Hello World!") == "hello_world"
        assert writer._sanitize_filename("Test@#$%") == "test"
        assert writer._sanitize_filename("Multiple   Spaces") == "multiple_spaces"


class TestSchemas:
    """Tests for Pydantic schemas."""
    
    def test_element_info(self):
        """Test ElementInfo model."""
        element = ElementInfo(
            selector="#myButton",
            tag_name="button",
            text_content="Click Me",
            classes=["btn", "primary"]
        )
        
        assert element.selector == "#myButton"
        assert element.tag_name == "button"
        assert "btn" in element.classes
    
    def test_hover_interaction(self):
        """Test HoverInteraction model."""
        trigger = ElementInfo(
            selector="nav a",
            tag_name="a",
            text_content="Menu"
        )
        
        interaction = HoverInteraction(
            trigger_element=trigger,
            revealed_links=[{"text": "Link 1", "href": "/link1"}]
        )
        
        assert interaction.trigger_element.text_content == "Menu"
        assert len(interaction.revealed_links) == 1
    
    def test_page_analysis(self):
        """Test PageAnalysis model."""
        analysis = PageAnalysis(
            url="https://example.com",
            page_title="Example",
            hover_interactions=[],
            popup_interactions=[]
        )
        
        assert analysis.url == "https://example.com"
        assert analysis.page_title == "Example"


# Integration test (requires playwright)
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires browser installation")
async def test_interaction_detector():
    """Integration test for interaction detector."""
    from src.analyzer.interaction_detector import InteractionDetector
    
    detector = InteractionDetector(headless=True)
    analysis = await detector.analyze_page("https://example.com")
    
    assert analysis.url == "https://example.com"
    assert analysis.page_title is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
