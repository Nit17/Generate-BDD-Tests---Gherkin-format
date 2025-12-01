"""
FastAPI application for BDD Test Generator.
Provides REST API endpoints for generating Gherkin tests.
"""

import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import asyncio
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzer.interaction_detector import InteractionDetector
from src.llm.gherkin_generator import GherkinGenerator
from src.output.feature_writer import FeatureWriter
from src.models.schemas import GenerationRequest, GenerationResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BDD Test Generator API",
    description="AI-powered API for generating Gherkin BDD test scenarios from website interactions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    """Request model for URL-based generation."""
    url: str
    include_hover: bool = True
    include_popups: bool = True
    headless: bool = True
    provider: str = "openai"


class GenerateResponse(BaseModel):
    """Response model for generation."""
    success: bool
    url: str
    feature_content: str
    file_path: Optional[str] = None
    hover_count: int = 0
    popup_count: int = 0
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "BDD Test Generator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate": "Generate Gherkin tests for a URL",
            "POST /analyze": "Analyze a URL without generating tests",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_tests(request: URLRequest):
    """
    Generate Gherkin BDD test scenarios for a given URL.
    
    This endpoint:
    1. Analyzes the webpage for interactive elements
    2. Detects hover and popup interactions
    3. Generates Gherkin scenarios using LLM
    4. Returns the feature file content
    """
    try:
        logger.info(f"Generating tests for: {request.url}")
        
        # Initialize components
        detector = InteractionDetector(headless=request.headless)
        
        # Analyze the page
        analysis = await detector.analyze_page(request.url)
        
        hover_count = len(analysis.hover_interactions)
        popup_count = len(analysis.popup_interactions)
        
        logger.info(f"Found {hover_count} hover and {popup_count} popup interactions")
        
        if hover_count == 0 and popup_count == 0:
            return GenerateResponse(
                success=True,
                url=request.url,
                feature_content="# No interactive elements detected on this page",
                hover_count=0,
                popup_count=0
            )
        
        # Generate Gherkin content
        try:
            generator = GherkinGenerator(provider=request.provider)
            feature_content = await generator.generate_combined_feature(analysis)
        except ValueError as e:
            # API key not set - use fallback
            logger.warning(f"LLM not available: {e}. Using fallback generator.")
            generator = GherkinGenerator.__new__(GherkinGenerator)
            feature_content = generator._generate_fallback_feature(analysis)
        
        # Write to file
        writer = FeatureWriter()
        file_path = writer.write_raw_content(feature_content, request.url)
        
        return GenerateResponse(
            success=True,
            url=request.url,
            feature_content=feature_content,
            file_path=file_path,
            hover_count=hover_count,
            popup_count=popup_count
        )
        
    except Exception as e:
        logger.error(f"Error generating tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_page(request: URLRequest):
    """
    Analyze a webpage for interactive elements without generating tests.
    
    Returns detailed information about detected interactions.
    """
    try:
        detector = InteractionDetector(headless=request.headless)
        analysis = await detector.analyze_page(request.url)
        
        return {
            "success": True,
            "url": analysis.url,
            "page_title": analysis.page_title,
            "metadata": analysis.metadata,
            "hover_interactions": [
                {
                    "trigger": h.trigger_element.text_content,
                    "revealed_links": h.revealed_links[:10],
                    "type": h.interaction_type.value
                }
                for h in analysis.hover_interactions
            ],
            "popup_interactions": [
                {
                    "trigger": p.trigger_element.text_content,
                    "popup_title": p.popup_title,
                    "buttons": p.action_buttons,
                    "type": p.interaction_type.value
                }
                for p in analysis.popup_interactions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quick-scan")
async def quick_scan(request: URLRequest):
    """
    Perform a quick DOM analysis without browser interaction testing.
    
    Faster but less accurate than full analysis.
    """
    try:
        detector = InteractionDetector(headless=request.headless)
        result = await detector.quick_scan(request.url)
        
        return {
            "success": True,
            "url": request.url,
            **result
        }
        
    except Exception as e:
        logger.error(f"Error in quick scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feature/{filename}")
async def get_feature_file(filename: str):
    """
    Download a generated feature file.
    """
    file_path = os.path.join("./output", f"{filename}.feature")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Feature file not found")
    
    return FileResponse(
        file_path,
        media_type="text/plain",
        filename=f"{filename}.feature"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
