#!/usr/bin/env python3
"""
BDD Test Generator - Command Line Interface
Generates Gherkin-style BDD test scenarios for websites.
"""

import argparse
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.analyzer.interaction_detector import InteractionDetector
from src.llm.gherkin_generator import GherkinGenerator
from src.output.feature_writer import FeatureWriter


async def main():
    parser = argparse.ArgumentParser(
        description="Generate BDD Gherkin tests from website interactions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --url "https://www.tivdak.com/patient-stories/"
  python main.py --url "https://www.nike.com/in/" --provider gemini
  python main.py --url "https://www.apple.com/in/" --output ./tests --no-headless
        """
    )
    
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="Website URL to analyze"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory for feature files (default: ./output)"
    )
    
    parser.add_argument(
        "--provider", "-p",
        choices=["openai", "gemini"],
        default="openai",
        help="LLM provider for Gherkin generation (default: openai)"
    )
    
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with visible window (default: headless)"
    )
    
    parser.add_argument(
        "--no-hover",
        action="store_true",
        help="Skip hover interaction detection"
    )
    
    parser.add_argument(
        "--no-popup",
        action="store_true",
        help="Skip popup interaction detection"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick scan without full interaction testing"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Ensure URL has protocol
    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print("=" * 60)
    print("🧪 BDD Test Generator - Gherkin Format")
    print("=" * 60)
    print(f"\n📍 URL: {url}")
    print(f"📁 Output: {args.output}")
    print(f"🤖 LLM Provider: {args.provider}")
    print(f"🖥️  Headless: {not args.no_headless}")
    print()
    
    try:
        # Initialize detector
        detector = InteractionDetector(
            headless=not args.no_headless,
            timeout=30000
        )
        
        if args.quick:
            print("🔍 Performing quick scan...")
            result = await detector.quick_scan(url)
            print(f"\n📊 Quick Scan Results:")
            print(f"   Navigation menus: {len(result.get('navigation_menus', []))}")
            print(f"   Interactive elements: {len(result.get('interactive_elements', []))}")
            print(f"   Dropdowns: {len(result.get('dropdowns', []))}")
            print(f"   Modal triggers: {len(result.get('modal_triggers', []))}")
            return
        
        # Full analysis
        print("🔍 Analyzing webpage...")
        print("   This may take a minute as we test interactions...\n")
        
        analysis = await detector.analyze_page(url)
        
        print(f"✅ Analysis complete!")
        print(f"   📄 Page: {analysis.page_title}")
        print(f"   🖱️  Hover interactions: {len(analysis.hover_interactions)}")
        print(f"   💬 Popup interactions: {len(analysis.popup_interactions)}")
        print()
        
        if len(analysis.hover_interactions) == 0 and len(analysis.popup_interactions) == 0:
            print("⚠️  No interactive elements detected on this page.")
            print("   The page might be static or require authentication.")
            return
        
        # Generate Gherkin
        print("🤖 Generating Gherkin scenarios...")
        
        try:
            generator = GherkinGenerator(provider=args.provider)
            feature_content = await generator.generate_combined_feature(analysis)
        except ValueError as e:
            print(f"⚠️  LLM not available: {e}")
            print("   Using fallback generator...")
            generator = GherkinGenerator.__new__(GherkinGenerator)
            feature_content = generator._generate_fallback_feature(analysis)
        
        # Write output
        writer = FeatureWriter(output_dir=args.output)
        file_path = writer.write_raw_content(feature_content, url)
        
        print(f"\n✅ Feature file generated!")
        print(f"   📁 Saved to: {file_path}")
        print()
        
        # Print the content
        print("=" * 60)
        print("📝 Generated Gherkin Scenarios:")
        print("=" * 60)
        print(feature_content)
        print("=" * 60)
        
        # Also save analysis report
        if args.verbose:
            report_path = writer.write_analysis_report(analysis)
            print(f"\n📊 Analysis report: {report_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
