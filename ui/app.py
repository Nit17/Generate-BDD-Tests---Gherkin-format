"""
Streamlit UI for BDD Test Generator.
Provides a user-friendly interface for generating Gherkin tests.
"""

import streamlit as st
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzer.interaction_detector import InteractionDetector
from src.llm.gherkin_generator import GherkinGenerator
from src.output.feature_writer import FeatureWriter


def run_async(coro):
    """Helper to run async functions in Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def main():
    st.set_page_config(
        page_title="BDD Test Generator",
        layout="wide"
    )
    
    st.title("BDD Test Generator")
    st.markdown("""
    Generate Gherkin-style BDD test scenarios from website interactions automatically.
    
    This tool analyzes webpages for:
    - **Hover interactions** (dropdowns, menus, tooltips)
    - **Popup/Modal interactions** (dialogs, confirmation prompts)
    """)
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    llm_provider = st.sidebar.selectbox(
        "LLM Provider",
        ["openai", "gemini"],
        help="Select the LLM provider for generating Gherkin scenarios"
    )
    
    headless = st.sidebar.checkbox(
        "Headless Mode",
        value=True,
        help="Run browser in headless mode (no visible window)"
    )
    
    api_key = st.sidebar.text_input(
        f"{llm_provider.upper()} API Key",
        type="password",
        help=f"Enter your {llm_provider} API key"
    )
    
    if api_key:
        if llm_provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            os.environ["GEMINI_API_KEY"] = api_key
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### Example URLs
    - https://www.tivdak.com/patient-stories/
    - https://www.nike.com/in/
    - https://www.apple.com/in/
    """)
    
    # Main content
    url = st.text_input(
        "Enter Website URL",
        placeholder="https://example.com",
        help="Enter the full URL of the website to analyze"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_hover = st.checkbox("Include Hover Interactions", value=True)
    with col2:
        include_popups = st.checkbox("Include Popup Interactions", value=True)
    with col3:
        save_to_file = st.checkbox("Save to .feature file", value=True)
    
    if st.button("Generate Tests", type="primary", use_container_width=True):
        if not url:
            st.error("Please enter a URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Initialize
            status_text.text("Initializing browser...")
            progress_bar.progress(10)
            
            detector = InteractionDetector(headless=headless)
            
            # Step 2: Analyze page
            status_text.text("Analyzing webpage...")
            progress_bar.progress(30)
            
            analysis = run_async(detector.analyze_page(url))
            
            progress_bar.progress(60)
            
            # Display analysis results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Page Title", analysis.page_title[:30] + "..." if len(analysis.page_title) > 30 else analysis.page_title)
            with col2:
                st.metric("Hover Interactions", len(analysis.hover_interactions))
            with col3:
                st.metric("Popup Interactions", len(analysis.popup_interactions))
            
            if len(analysis.hover_interactions) == 0 and len(analysis.popup_interactions) == 0:
                st.warning("No interactive elements detected on this page.")
                progress_bar.progress(100)
                status_text.text("Complete - No interactions found")
                return
            
            # Step 3: Generate Gherkin
            status_text.text("Generating Gherkin scenarios...")
            progress_bar.progress(80)
            
            try:
                generator = GherkinGenerator(provider=llm_provider)
                feature_content = run_async(generator.generate_combined_feature(analysis))
            except ValueError as e:
                st.warning(f"LLM not available ({e}). Using fallback generator.")
                generator = GherkinGenerator.__new__(GherkinGenerator)
                feature_content = generator._generate_fallback_feature(analysis)
            
            progress_bar.progress(90)
            
            # Step 4: Output
            status_text.text("Formatting output...")
            
            # Display the generated feature
            st.subheader("Generated Gherkin Scenarios")
            st.code(feature_content, language="gherkin")
            
            # Save to file if requested
            if save_to_file:
                writer = FeatureWriter()
                file_path = writer.write_raw_content(feature_content, url)
                st.success(f"Feature file saved to: {file_path}")
            
            # Download button
            st.download_button(
                label="Download .feature file",
                data=feature_content,
                file_name="generated_tests.feature",
                mime="text/plain"
            )
            
            progress_bar.progress(100)
            status_text.text("Generation complete!")
            
            # Show detailed analysis in expander
            with st.expander("Detailed Analysis"):
                st.json({
                    "url": analysis.url,
                    "metadata": analysis.metadata,
                    "hover_interactions": [
                        {
                            "trigger": h.trigger_element.text_content,
                            "revealed_links": h.revealed_links[:5]
                        }
                        for h in analysis.hover_interactions[:5]
                    ],
                    "popup_interactions": [
                        {
                            "trigger": p.trigger_element.text_content,
                            "popup_title": p.popup_title,
                            "buttons": p.action_buttons
                        }
                        for p in analysis.popup_interactions[:5]
                    ]
                })
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Built with Playwright, OpenAI/Gemini, and Streamlit</p>
        <p><a href="https://cucumber.io/docs/gherkin/" target="_blank">Gherkin Reference</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
