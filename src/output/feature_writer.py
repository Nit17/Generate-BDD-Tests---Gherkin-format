"""
Feature Writer module.
Handles writing Gherkin features to .feature files.
"""

import os
import re
from typing import List, Optional
from datetime import datetime
import logging

from ..models.schemas import GherkinFeature, PageAnalysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureWriter:
    """
    Writes Gherkin features to .feature files.
    """

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the feature writer.
        
        Args:
            output_dir: Directory to write feature files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Convert a string to a valid filename."""
        # Remove or replace invalid characters
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)
        return name.lower()[:50]

    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL."""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return self._sanitize_filename(domain.split('.')[0])

    def write_feature(
        self, 
        feature: GherkinFeature, 
        filename: Optional[str] = None
    ) -> str:
        """
        Write a single feature to a file.
        
        Args:
            feature: GherkinFeature to write
            filename: Optional filename (without extension)
            
        Returns:
            Path to the written file
        """
        if filename is None:
            filename = self._sanitize_filename(feature.name)
        
        filepath = os.path.join(self.output_dir, f"{filename}.feature")
        
        content = self._format_feature(feature)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Written feature file: {filepath}")
        return filepath

    def write_features(
        self, 
        features: List[GherkinFeature], 
        combined: bool = True,
        base_filename: Optional[str] = None
    ) -> List[str]:
        """
        Write multiple features to files.
        
        Args:
            features: List of GherkinFeature objects
            combined: If True, write all to one file; if False, separate files
            base_filename: Base name for the file(s)
            
        Returns:
            List of paths to written files
        """
        if not features:
            logger.warning("No features to write")
            return []
        
        paths = []
        
        if combined:
            filename = base_filename or "generated_tests"
            filepath = os.path.join(self.output_dir, f"{filename}.feature")
            
            content_parts = []
            for i, feature in enumerate(features):
                if i > 0:
                    content_parts.append("\n\n")
                content_parts.append(self._format_feature(feature))
            
            content = ''.join(content_parts)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Written combined feature file: {filepath}")
            paths.append(filepath)
        else:
            for feature in features:
                path = self.write_feature(feature)
                paths.append(path)
        
        return paths

    def write_raw_content(
        self, 
        content: str, 
        url: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Write raw Gherkin content to a file.
        
        Args:
            content: Raw Gherkin content
            url: Source URL (used for filename if not provided)
            filename: Optional filename
            
        Returns:
            Path to the written file
        """
        if filename is None:
            domain = self._get_domain_from_url(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{domain}_tests_{timestamp}"
        
        filepath = os.path.join(self.output_dir, f"{filename}.feature")
        
        # Add header comment
        header = f"""# Auto-generated BDD Test Scenarios
# Source URL: {url}
# Generated: {datetime.now().isoformat()}
# Generator: BDD Test Generator

"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header + content)
        
        logger.info(f"Written feature file: {filepath}")
        return filepath

    def _format_feature(self, feature: GherkinFeature) -> str:
        """
        Format a GherkinFeature object to proper Gherkin syntax.
        """
        lines = []
        
        # Tags
        if feature.tags:
            lines.append(' '.join(feature.tags))
        
        # Feature
        lines.append(f"Feature: {feature.name}")
        
        # Description
        if feature.description:
            for desc_line in feature.description.split('\n'):
                lines.append(f"  {desc_line.strip()}")
            lines.append("")
        
        # Scenarios
        for scenario in feature.scenarios:
            lines.append("")
            
            # Scenario tags
            if scenario.tags:
                lines.append(f"  {' '.join(scenario.tags)}")
            
            lines.append(f"  Scenario: {scenario.name}")
            
            for step in scenario.steps:
                lines.append(f"    {step}")
        
        return '\n'.join(lines)

    def get_feature_content(self, features: List[GherkinFeature]) -> str:
        """
        Get the formatted content without writing to file.
        
        Args:
            features: List of GherkinFeature objects
            
        Returns:
            Formatted Gherkin content
        """
        content_parts = []
        for i, feature in enumerate(features):
            if i > 0:
                content_parts.append("\n\n")
            content_parts.append(self._format_feature(feature))
        
        return ''.join(content_parts)

    def write_analysis_report(
        self, 
        analysis: PageAnalysis, 
        filename: Optional[str] = None
    ) -> str:
        """
        Write a JSON report of the page analysis.
        
        Args:
            analysis: PageAnalysis object
            filename: Optional filename
            
        Returns:
            Path to the written file
        """
        import json
        
        if filename is None:
            domain = self._get_domain_from_url(analysis.url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{domain}_analysis_{timestamp}"
        
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        
        # Convert to dict
        report = {
            'url': analysis.url,
            'page_title': analysis.page_title,
            'generated_at': datetime.now().isoformat(),
            'hover_interactions_count': len(analysis.hover_interactions),
            'popup_interactions_count': len(analysis.popup_interactions),
            'metadata': analysis.metadata,
            'hover_interactions': [
                {
                    'trigger': h.trigger_element.text_content,
                    'revealed_links_count': len(h.revealed_links),
                    'revealed_links': h.revealed_links[:5]
                }
                for h in analysis.hover_interactions
            ],
            'popup_interactions': [
                {
                    'trigger': p.trigger_element.text_content,
                    'popup_title': p.popup_title,
                    'buttons': p.action_buttons
                }
                for p in analysis.popup_interactions
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Written analysis report: {filepath}")
        return filepath
