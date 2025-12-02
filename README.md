# Generate BDD Tests - Gherkin Format

An AI-powered automation solution that dynamically generates Gherkin-style BDD test scenarios for websites containing hovering elements, popups, and interactive components.

## Features

- **Dynamic Element Detection**: Automatically detects hoverable elements, popups, dropdowns, and modals
- **AI-Powered Generation**: Uses LLMs (OpenAI GPT-4/Gemini) to generate clean Gherkin scenarios
- **Browser Automation**: Playwright-based automation for simulating user interactions
- **Gherkin Output**: Generates well-formatted `.feature` files following Cucumber specification
- **FastAPI Backend**: REST API for easy integration
- **Streamlit UI**: Optional web interface for easy use
- **Parallel Execution**: Optimized with concurrent hover/click testing
- **Response Caching**: LRU caching for LLM responses to reduce API calls
- **Centralized Configuration**: All settings managed from a single config file

## Quick Start (New Device Setup)

### Prerequisites

- **Python 3.9+** (tested with Python 3.13)
- **Git**
- **Internet connection** (for LLM API calls)

### Step-by-Step Installation

```bash
# Step 1: Clone the repository
git clone https://github.com/Nit17/Generate-BDD-Tests---Gherkin-format.git
cd Generate-BDD-Tests---Gherkin-format

# Step 2: Create and activate virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Step 3: Install Python dependencies
pip install -r requirements.txt

# Step 4: Install Playwright browser (required for web automation)
playwright install chromium

# Step 5: Set up environment variables
cp .env.example .env
# Edit .env file and add your API key (see Configuration section below)

# Step 6: Verify installation
python -c "from src import ServiceFactory; print('Installation successful!')"
```

### Running the Application

After installation, you can run the application in three ways:

#### Option 1: Command Line (Recommended for quick use)
```bash
python main.py --url "https://example.com" --provider gemini
```

#### Option 2: Web UI (Recommended for beginners)
```bash
streamlit run ui/app.py
# Open http://localhost:8501 in your browser
```

#### Option 3: REST API (Recommended for integration)
```bash
uvicorn api.main:app --reload --port 8000
# API available at http://localhost:8000
```

## Project Structure

```
├── src/
│   ├── __init__.py
│   ├── config.py              # Centralized configuration (NEW)
│   ├── factory.py             # Dependency injection factory
│   ├── interfaces/            # Abstract base classes (SOLID)
│   │   ├── browser.py
│   │   ├── analyzer.py
│   │   ├── llm.py
│   │   └── output.py
│   ├── browser/
│   │   ├── __init__.py
│   │   └── automation.py      # Playwright-based browser automation
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── dom_analyzer.py    # DOM structure analysis
│   │   └── interaction_detector.py  # Parallel hover/popup detection
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── providers.py       # OpenAI/Gemini providers with caching
│   │   └── gherkin_generator.py  # LLM-based Gherkin generation
│   ├── output/
│   │   ├── __init__.py
│   │   └── feature_writer.py  # .feature file writer
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   └── utils/
│       ├── __init__.py
│       └── cache.py           # LRU caching utilities (NEW)
├── api/
│   ├── __init__.py
│   └── main.py                # FastAPI application
├── ui/
│   └── app.py                 # Streamlit UI
├── output/                    # Generated .feature files
├── tests/
│   └── test_generator.py
├── main.py                    # CLI entry point
├── requirements.txt
├── .env.example
├── DOCUMENTATION.md           # Detailed documentation
└── README.md
```

## Configuration

### Environment Variables

Create a `.env` file with your API keys:

```env
# LLM Provider API Key (choose one)
OPENAI_API_KEY=your_openai_api_key
# OR
GEMINI_API_KEY=your_gemini_api_key

# Optional settings
LLM_PROVIDER=gemini   # Options: 'openai' or 'gemini' (default: gemini)
HEADLESS=true         # Run browser in headless mode (default: true)
```

### Getting API Keys

| Provider | How to Get Key |
|----------|---------------|
| **Gemini** (Recommended - Free tier available) | Visit [Google AI Studio](https://aistudio.google.com/apikey) |
| **OpenAI** | Visit [OpenAI Platform](https://platform.openai.com/api-keys) |

### Centralized Configuration

All configurable settings are in `src/config.py`:

```python
# Browser settings
BrowserConfig:
  - DEFAULT_TIMEOUT: 30000ms
  - HEADLESS: true
  - VIEWPORT: 1920x1080

# Detection limits
DetectorConfig:
  - MAX_HOVER_ELEMENTS: 15
  - MAX_POPUP_BUTTONS: 10
  - CONCURRENT_HOVER_LIMIT: 3

# LLM settings
LLMConfig:
  - GEMINI_MODEL: "gemini-2.0-flash"
  - OPENAI_MODEL: "gpt-4"
  - TEMPERATURE: 0.3
```

## Usage

### Command Line Interface

```bash
# Basic usage with Gemini (default)
python main.py --url "https://www.example.com"

# Specify LLM provider
python main.py --url "https://www.example.com" --provider openai

# Custom output directory
python main.py --url "https://www.example.com" --output ./my-tests

# Show browser window (non-headless)
python main.py --url "https://www.example.com" --no-headless
```

### FastAPI Backend

```bash
# Start the API server
uvicorn api.main:app --reload --port 8000
```

**API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Health check |
| `POST` | `/generate` | Generate Gherkin tests |
| `GET` | `/generate` | Generate tests via query params |

**Example API Request:**
```bash
# POST request
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com"}'

# GET request
curl "http://localhost:8000/generate?url=https://www.example.com"
```

### Streamlit UI

```bash
streamlit run ui/app.py
```

Then open `http://localhost:8501` in your browser.

The UI provides:
- URL input field
- LLM provider selection (OpenAI/Gemini)
- Real-time status updates
- Preview of generated Gherkin scenarios
- Download button for .feature files

## How It Works

1. **URL Input**: The system accepts a website URL
2. **Browser Automation**: Uses Playwright to load the page and simulate interactions
3. **DOM Analysis**: Analyzes the page structure to identify:
   - Navigation menus with hover dropdowns
   - Buttons that trigger popups/modals
   - Tooltip elements
   - Image overlays
4. **Interaction Simulation**: Hovers over detected elements to reveal hidden content
5. **LLM Processing**: Sends interaction data to an LLM to generate Gherkin scenarios
6. **Output Generation**: Creates well-formatted `.feature` files

## Example Output

### Input URL
`https://www.tivdak.com/patient-stories/`

### Generated Gherkin Scenarios

```gherkin
Feature: Validate "Learn More" pop-up functionality

  Scenario: Verify the cancel button in the "You are now leaving tivdak.com" pop-up
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user clicks the "Learn More" button
    Then a pop-up should appear with the title "You are now leaving tivdak.com"
    When the user clicks the "Cancel" button
    Then the pop-up should close and the user should remain on the same page

  Scenario: Verify the continue button navigates to external site
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user clicks the "Learn More" button
    Then a pop-up should appear with the title "You are now leaving tivdak.com"
    When the user clicks the "Continue" button
    Then the page URL should change to "https://alishasjourney.com/"

Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "Patient Stories" to "What is Tivdak?" page
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "About Tivdak"
    And clicks the link "What is Tivdak?" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/about-tivdak/"
```

## Supported Interaction Types

| Type | Description |
|------|-------------|
| Hover Dropdowns | Navigation menus that reveal submenus on hover |
| Popups/Modals | Dialogs triggered by button clicks |
| Tooltips | Information boxes appearing on hover |
| Image Overlays | Content revealed on image hover |
| Accordion Elements | Expandable content sections |

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                     │
├─────────────────────┬─────────────────────┬─────────────────────────────────────┤
│      CLI            │    FastAPI          │         Streamlit UI                │
│    main.py          │   api/main.py       │         ui/app.py                   │
│                     │                     │                                     │
│  python main.py     │  POST /generate     │  Browser-based                      │
│  --url <url>        │  POST /analyze      │  Interactive Form                   │
└─────────┬───────────┴──────────┬──────────┴──────────────┬──────────────────────┘
          │                      │                         │
          └──────────────────────┼─────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INTERACTION DETECTOR                                     │
│                   src/analyzer/interaction_detector.py                          │
│                                                                                 │
│  • Coordinates browser automation and DOM analysis                              │
│  • Detects hover interactions (dropdowns, tooltips)                             │
│  • Detects popup/modal interactions                                             │
│  • Returns PageAnalysis object                                                  │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│  BROWSER AUTOMATION │ │  DOM ANALYZER   │ │   ELEMENT           │
│  src/browser/       │ │  src/analyzer/  │ │   EXTRACTOR         │
│  automation.py      │ │  dom_analyzer.py│ │                     │
│                     │ │                 │ │                     │
│  • Playwright       │ │  • BeautifulSoup│ │  • Get element info │
│  • Navigate pages   │ │  • Parse HTML   │ │  • CSS selectors    │
│  • Hover elements   │ │  • Find elements│ │  • ARIA attributes  │
│  • Click buttons    │ │  • Structure    │ │  • Bounding boxes   │
│  • Detect popups    │ │    analysis     │ │                     │
└─────────────────────┘ └─────────────────┘ └─────────────────────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PAGE ANALYSIS                                       │
│                          src/models/schemas.py                                   │
│                                                                                 │
│  PageAnalysis {                                                                 │
│    url: str                                                                     │
│    page_title: str                                                              │
│    hover_interactions: List[HoverInteraction]                                   │
│    popup_interactions: List[PopupInteraction]                                   │
│    navigation_elements: List[ElementInfo]                                       │
│    metadata: Dict                                                               │
│  }                                                                              │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GHERKIN GENERATOR                                      │
│                      src/llm/gherkin_generator.py                               │
│                                                                                 │
│  • Transforms PageAnalysis into Gherkin scenarios                               │
│  • Uses LLM for natural language generation                                     │
│  • Follows Cucumber Gherkin specification                                       │
│  • Fallback template generation if LLM unavailable                              │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│       LLM PROVIDERS           │ │     FALLBACK GENERATOR        │
│    src/llm/providers.py       │ │                               │
│                               │ │  Template-based generation    │
│  ┌─────────────────────────┐  │ │  when LLM is unavailable      │
│  │    ILLMProvider         │  │ │                               │
│  │    (Interface)          │  │ └───────────────────────────────┘
│  └───────────┬─────────────┘  │
│              │                │
│    ┌─────────┴─────────┐      │
│    │                   │      │
│    ▼                   ▼      │
│ ┌────────────┐ ┌────────────┐ │
│ │  OpenAI    │ │  Gemini    │ │
│ │  Provider  │ │  Provider  │ │
│ │            │ │            │ │
│ │  GPT-4     │ │ gemini-2.0 │ │
│ │            │ │   -flash   │ │
│ └────────────┘ └────────────┘ │
└───────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            FEATURE WRITER                                        │
│                      src/output/feature_writer.py                               │
│                                                                                 │
│  • Formats Gherkin content                                                      │
│  • Writes .feature files with timestamps                                        │
│  • Generates analysis reports (JSON)                                            │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               OUTPUT                                             │
│                           output/*.feature                                       │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Feature: Validate navigation menu functionality                         │    │
│  │                                                                         │    │
│  │   Scenario: Verify dropdown menu appears on hover                       │    │
│  │     Given the user is on the "https://example.com" page                 │    │
│  │     When the user hovers over the navigation menu "Products"            │    │
│  │     Then a dropdown menu should appear                                  │    │
│  │     And the dropdown should contain "Product A"                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   URL    │────▶│   Browser    │────▶│   Detect     │────▶│   Generate   │
│  Input   │     │   Navigate   │     │ Interactions │     │   Gherkin    │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                        │                    │                    │
                        ▼                    ▼                    ▼
                 ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                 │  Dismiss     │     │  Hover &     │     │   LLM API    │
                 │  Cookies     │     │  Click Test  │     │   Call       │
                 └──────────────┘     └──────────────┘     └──────────────┘
                        │                    │                    │
                        ▼                    ▼                    ▼
                 ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                 │  Extract     │     │  Build       │     │   Format &   │
                 │  HTML/DOM    │     │ PageAnalysis │     │   Save       │
                 └──────────────┘     └──────────────┘     └──────────────┘
```

### Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                      ServiceFactory (DIP)                        │
│                        src/factory.py                            │
│                                                                 │
│   Creates and injects dependencies for all components           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ IBrowserAuto-   │    │ ILLMProvider    │    │ IFeatureWriter  │
│ mation          │    │                 │    │                 │
│ (Interface)     │    │ (Interface)     │    │ (Interface)     │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ BrowserAuto-    │    │ OpenAIProvider  │    │ FeatureWriter   │
│ mation          │    │ GeminiProvider  │    │                 │
│ (Implementation)│    │ (Implementations│    │ (Implementation)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### SOLID Principles

This project follows SOLID design principles for maintainable and extensible code:

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility (SRP)** | Each class has one job: `BrowserAutomation` handles browser control, `DOMAnalyzer` parses HTML, `GherkinGenerator` creates tests |
| **Open/Closed (OCP)** | New LLM providers can be added without modifying existing code - just implement `ILLMProvider` |
| **Liskov Substitution (LSP)** | All LLM providers (`OpenAIProvider`, `GeminiProvider`, `MockLLMProvider`) are interchangeable |
| **Interface Segregation (ISP)** | Focused interfaces: `IBrowserAutomation`, `IDOMAnalyzer`, `ILLMProvider`, `IFeatureWriter` |
| **Dependency Inversion (DIP)** | High-level modules depend on abstractions via `ServiceFactory` for dependency injection |

### Project Structure

```
src/
├── interfaces/           # Abstract base classes (DIP)
│   ├── browser.py       # IBrowserAutomation
│   ├── analyzer.py      # IDOMAnalyzer, IInteractionDetector
│   ├── llm.py           # ILLMProvider, IGherkinGenerator
│   └── output.py        # IFeatureWriter
├── browser/
│   └── automation.py    # Playwright implementation
├── analyzer/
│   ├── dom_analyzer.py  # BeautifulSoup implementation
│   └── interaction_detector.py
├── llm/
│   ├── providers.py     # OpenAI, Gemini, Mock providers
│   └── gherkin_generator.py
├── output/
│   └── feature_writer.py
├── models/
│   └── schemas.py       # Pydantic models
└── factory.py           # ServiceFactory for DI
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Browser Automation | Playwright | Headless browser control, hover/click simulation |
| HTML Parsing | BeautifulSoup, lxml | DOM analysis and element extraction |
| LLM Integration | OpenAI GPT-4 / Google Gemini | AI-powered Gherkin generation |
| Backend API | FastAPI | REST API endpoints |
| UI | Streamlit | Web-based user interface |
| Data Models | Pydantic | Request/response validation |
| Caching | Custom LRU Cache | Response caching for performance |

## Performance Optimizations

The codebase includes several performance optimizations:

| Optimization | Description |
|--------------|-------------|
| **Parallel Hover Testing** | Uses `asyncio.gather` with semaphore to test multiple hovers concurrently |
| **Combined CSS Selectors** | Single selector query instead of multiple sequential queries |
| **LLM Response Caching** | LRU cache prevents duplicate API calls for same prompts |
| **Element Caching** | Caches element lookup results during page analysis |
| **Centralized Config** | All magic numbers in one place for easy tuning |
| **Text Normalization** | Pydantic validators auto-clean whitespace from extracted text for clean output |

## Troubleshooting

### Common Issues

**1. "playwright install chromium" fails**
```bash
# Try with sudo on Linux/macOS
sudo playwright install chromium

# Or install dependencies first
playwright install-deps chromium
```

**2. "Import could not be resolved" errors in IDE**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**3. LLM API errors**
```bash
# Verify API key is set
echo $GEMINI_API_KEY  # or $OPENAI_API_KEY

# Test API key
python -c "from src.llm.providers import GeminiProvider; print('OK')"
```

**4. Browser timeout errors**
```bash
# Increase timeout in src/config.py
# Or run with visible browser to debug
python main.py --url "https://example.com" --no-headless
```

**5. No interactions detected**
- Some websites block automated browsers
- Try a different website to verify setup
- Check if the website uses JavaScript frameworks that need more load time

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src

# Run specific test
python -m pytest tests/test_generator.py::TestDOMAnalyzer -v
```
