# Generate BDD Tests - Gherkin Format

An AI-powered automation solution that dynamically generates Gherkin-style BDD test scenarios for websites containing hovering elements, popups, and interactive components.

## Features

- **Dynamic Element Detection**: Automatically detects hoverable elements, popups, dropdowns, and modals
- **AI-Powered Generation**: Uses LLMs (OpenAI GPT-4/Gemini) to generate clean Gherkin scenarios
- **Browser Automation**: Playwright-based automation for simulating user interactions
- **Gherkin Output**: Generates well-formatted `.feature` files
- **FastAPI Backend**: REST API for easy integration
- **Streamlit UI**: Optional web interface for easy use

## Project Structure

```
├── src/
│   ├── __init__.py
│   ├── browser/
│   │   ├── __init__.py
│   │   └── automation.py      # Playwright-based browser automation
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── dom_analyzer.py    # DOM structure analysis
│   │   └── interaction_detector.py  # Hover/popup detection
│   ├── llm/
│   │   ├── __init__.py
│   │   └── gherkin_generator.py  # LLM-based Gherkin generation
│   ├── output/
│   │   ├── __init__.py
│   │   └── feature_writer.py  # .feature file writer
│   └── models/
│       ├── __init__.py
│       └── schemas.py         # Pydantic models
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
└── README.md
```

## Installation

### Prerequisites

- Python 3.9+
- Chrome/Chromium browser

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nit17/Generate-BDD-Tests---Gherkin-format.git
   cd Generate-BDD-Tests---Gherkin-format
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

## Configuration

Create a `.env` file with your API keys:

```env
# Choose one LLM provider
OPENAI_API_KEY=your_openai_api_key
# OR
GEMINI_API_KEY=your_gemini_api_key

# Optional settings
LLM_PROVIDER=openai  # or 'gemini'
HEADLESS=true        # Run browser in headless mode
```

## Usage

### Command Line Interface

```bash
# Basic usage
python main.py --url "https://www.tivdak.com/patient-stories/"

# With options
python main.py --url "https://www.nike.com/in/" --output ./output --provider openai
```

### FastAPI Backend

```bash
# Start the API server
uvicorn api.main:app --reload --port 8000
```

API Endpoints:
- `POST /generate` - Generate Gherkin tests for a URL
- `GET /health` - Health check

Example request:
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tivdak.com/patient-stories/"}'
```

### Streamlit UI

```bash
streamlit run ui/app.py
```

Then open `http://localhost:8501` in your browser.

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

## Tech Stack

| Layer | Technology |
|-------|------------|
| Browser Automation | Playwright |
| HTML Parsing | BeautifulSoup, lxml |
| LLM Integration | OpenAI GPT-4 / Google Gemini |
| Backend API | FastAPI |
| UI | Streamlit |
| Data Models | Pydantic |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Cucumber - Gherkin Reference](https://cucumber.io/docs/gherkin/)
- [Playwright Python](https://playwright.dev/python/)
- [OpenAI API](https://platform.openai.com/docs/)
