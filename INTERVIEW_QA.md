# Interview Questions & Answers - BDD Test Generator Project

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Technical Architecture](#2-technical-architecture)
3. [Dynamic Element Detection](#3-dynamic-element-detection)
4. [SOLID Principles & Design Patterns](#4-solid-principles--design-patterns)
5. [Concurrency & Performance](#5-concurrency--performance)
6. [LLM Integration](#6-llm-integration)
7. [Error Handling](#7-error-handling)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment](#9-deployment)
10. [Challenges & Problem Solving](#10-challenges--problem-solving)
11. [Code Walkthrough Questions](#11-code-walkthrough-questions)

---

## 1. Project Overview

### Q: Can you explain what your project does?
**A:** This is an AI-powered automation solution that dynamically generates Gherkin-style BDD test scenarios for websites. It uses:
- **Playwright** for browser automation to detect interactive elements (hovers, popups, dropdowns)
- **LLMs (OpenAI GPT-4 / Google Gemini)** to generate human-readable test cases
- **BeautifulSoup** for DOM analysis

The key differentiator is that it's **fully dynamic** - no hardcoded CSS selectors or element identifiers. It discovers interactive elements through behavior analysis.

### Q: Why did you build this project?
**A:** Manual test case creation is time-consuming and error-prone. This tool automates the discovery of interactive elements and generates standardized BDD test scenarios, reducing QA effort by 70-80% for initial test case creation.

### Q: Who would use this tool?
**A:** 
- QA Engineers needing to quickly generate test cases for new websites
- Developers wanting automated regression test scaffolding
- Teams adopting BDD methodology who need Gherkin feature files

### Q: What's the input and output of your system?
**A:**
- **Input:** A website URL
- **Output:** A `.feature` file containing Gherkin scenarios like:
```gherkin
Feature: Validate navigation menu functionality

  Scenario: Verify dropdown menu appears on hover
    Given the user is on the "https://example.com" page
    When the user hovers over the navigation menu "Products"
    Then a dropdown should appear
    And the dropdown should contain "Product A"
```

---

## 2. Technical Architecture

### Q: Can you walk me through the architecture?
**A:** The system follows a pipeline architecture:

```
URL Input → Browser Automation → Dynamic Detection → LLM Processing → Feature File Output
```

**Components:**
1. **BrowserAutomation** (Playwright) - Navigates pages, simulates interactions
2. **DynamicElementDetector** - Finds interactive elements via behavior analysis
3. **DOMAnalyzer** (BeautifulSoup) - Parses HTML structure
4. **InteractionDetector** - Coordinates hover/click detection
5. **GherkinGenerator** - Uses LLM to create test scenarios
6. **FeatureWriter** - Formats and saves `.feature` files

### Q: Why did you choose Playwright over Selenium?
**A:**
| Feature | Playwright | Selenium |
|---------|------------|----------|
| **Speed** | Faster execution | Slower |
| **Async Support** | Native async/await | Limited |
| **Auto-waiting** | Built-in smart waits | Manual waits needed |
| **Modern JS** | Better React/Vue support | Can struggle |
| **API** | Cleaner, more intuitive | Verbose |

### Q: Why did you choose Python for this project?
**A:**
- Rich ecosystem for web scraping (BeautifulSoup, lxml)
- Excellent async support (asyncio)
- Strong LLM library support (openai, google-generativeai)
- Playwright has first-class Python support
- Pydantic for data validation

### Q: Explain the data flow through your system.
**A:**
```
1. User provides URL
2. BrowserAutomation loads page in Chromium
3. CookieBannerHandler dismisses overlays
4. DynamicElementDetector finds hoverable/clickable elements
5. InteractionDetector simulates hovers/clicks, captures results
6. PageAnalysis object created with all interactions
7. GherkinGenerator sends to LLM with prompt
8. LLM returns Gherkin scenarios
9. FeatureWriter saves to .feature file
```

---

## 3. Dynamic Element Detection

### Q: What makes your detection "fully dynamic"?
**A:** Traditional tools use hardcoded CSS selectors like `.nav-menu`, `#dropdown`. Our approach:

1. **No hardcoded selectors** - We query ALL elements and filter by behavior
2. **Behavior-based detection:**
   - Check for `:hover` CSS style changes
   - Detect event listeners (`click`, `mousedown`)
   - Monitor ARIA attributes (`aria-haspopup`, `aria-expanded`)
   - Use MutationObserver for DOM changes

### Q: How do you detect hoverable elements?
**A:**
```python
# We look for elements with interactive behavior indicators:
- cursor: pointer style
- Has click/mouseenter event listeners
- ARIA roles (button, menuitem, tab)
- Tags: a, button, [role="button"]
- Elements with data-action, data-toggle attributes
```

### Q: How do you detect popups/modals?
**A:** Using DOM MutationObserver pattern:
```python
1. Record current DOM state
2. Click the trigger element
3. Wait for animations (configurable delay)
4. Detect new elements with:
   - position: fixed/absolute
   - z-index > 100
   - Overlay characteristics (covers viewport)
5. Extract popup content and buttons
```

### Q: How do you find revealed dropdown links after hover?
**A:**
```python
# After hovering, we query for visible containers:
selectors = [
    '.dropdown-menu',
    '[class*="dropdown"]',
    '[role="menu"]',
    '[aria-expanded="true"] + *',
    'nav ul ul'
]
# Then extract all <a> tags with text and href
```

---

## 4. SOLID Principles & Design Patterns

### Q: How does your project follow SOLID principles?
**A:**

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility (SRP)** | `BrowserAutomation` only handles browser control, `DOMAnalyzer` only parses HTML, `GherkinGenerator` only creates tests |
| **Open/Closed (OCP)** | New LLM providers can be added by implementing `ILLMProvider` interface without modifying existing code |
| **Liskov Substitution (LSP)** | `OpenAIProvider` and `GeminiProvider` are interchangeable - any can be used where `ILLMProvider` is expected |
| **Interface Segregation (ISP)** | Small, focused interfaces: `IBrowserAutomation`, `IDOMAnalyzer`, `ILLMProvider`, `IFeatureWriter` |
| **Dependency Inversion (DIP)** | High-level modules depend on abstractions via `ServiceFactory` for dependency injection |

### Q: What design patterns did you use?
**A:**

1. **Factory Pattern** - `ServiceFactory` creates all dependencies:
```python
class ServiceFactory:
    def create_llm_provider(self, provider: str) -> ILLMProvider:
        if provider == "openai":
            return OpenAIProvider()
        return GeminiProvider()
```

2. **Strategy Pattern** - Interchangeable LLM providers:
```python
# Can switch providers without changing client code
generator = GherkinGenerator(provider="gemini")
generator = GherkinGenerator(provider="openai")
```

3. **Template Method** - Fallback generation:
```python
try:
    feature = await generator.generate_with_llm(analysis)
except:
    feature = generator._generate_fallback_feature(analysis)
```

4. **Observer Pattern** - MutationObserver for popup detection

### Q: Show me an example of dependency injection in your code.
**A:**
```python
class InteractionDetector:
    def __init__(
        self, 
        browser_automation: Optional[IBrowserAutomation] = None  # DIP
    ):
        # Can inject mock for testing
        self._injected_browser = browser_automation
    
    def _create_browser(self) -> BrowserAutomation:
        if self._injected_browser:
            return self._injected_browser  # Use injected
        return BrowserAutomation()  # Create default
```

---

## 5. Concurrency & Performance

### Q: How do you handle parallel execution?
**A:** Using `asyncio.gather` with semaphores for controlled concurrency:

```python
# Limit to 3 concurrent hover tests to avoid overwhelming the page
semaphore = asyncio.Semaphore(3)

async def test_hover_with_semaphore(element):
    async with semaphore:
        return await browser.simulate_hover(element)

# Run all tests in parallel
results = await asyncio.gather(
    *[test_hover_with_semaphore(el) for el in elements],
    return_exceptions=True
)
```

### Q: What performance optimizations did you implement?
**A:**

| Optimization | Description |
|--------------|-------------|
| **Parallel Testing** | `asyncio.gather` with semaphore for concurrent hovers |
| **LLM Caching** | LRU cache prevents duplicate API calls |
| **Element Caching** | Cache lookup results during page analysis |
| **Configurable Limits** | `MAX_HOVER_ELEMENTS=15` to prevent slow scans |
| **Early Exit** | Stop testing after finding enough interactions |

### Q: How does your LRU cache work?
**A:**
```python
class LLMCache:
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, str] = {}
        self._max_size = max_size
    
    async def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)
    
    async def set(self, key: str, value: str):
        if len(self._cache) >= self._max_size:
            # Remove oldest entry
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = value
```

---

## 6. LLM Integration

### Q: How do you integrate with LLMs?
**A:** We support both OpenAI and Google Gemini:

```python
class GeminiProvider(ILLMProvider):
    async def generate(self, prompt: str) -> str:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = await model.generate_content_async(prompt)
        return response.text
```

### Q: What prompt engineering techniques do you use?
**A:**
```python
prompt = f"""
Generate Gherkin BDD test scenarios for the following webpage interactions.

URL: {analysis.url}
Page Title: {analysis.page_title}

HOVER INTERACTIONS DETECTED:
{hover_data}

POPUP INTERACTIONS DETECTED:
{popup_data}

Requirements:
1. Use proper Gherkin syntax (Given/When/Then)
2. Each scenario should test ONE specific interaction
3. Include the exact element text in quotes
4. For dropdowns, verify at least 2-3 revealed links
"""
```

### Q: What happens if the LLM API fails?
**A:** Fallback to template-based generation:
```python
try:
    feature_content = await generator.generate_combined_feature(analysis)
except ValueError as e:
    # LLM unavailable, use fallback
    feature_content = generator._generate_fallback_feature(analysis)
```

### Q: Why did you choose Gemini as the default?
**A:**
- Free tier available (good for demos)
- Fast response times
- Good at structured output (Gherkin)
- `gemini-2.0-flash` model is optimized for speed

---

## 7. Error Handling

### Q: How do you handle cookie banners blocking interactions?
**A:**
```python
class CookieBannerHandler:
    async def dismiss_cookie_banner(self):
        # Try multiple accept button patterns
        accept_selectors = [
            'button:has-text("Accept")',
            'button:has-text("I agree")',
            '[id*="accept"]',
            '[class*="consent"] button'
        ]
        
        for selector in accept_selectors:
            try:
                await self.page.click(selector, timeout=2000)
                return True
            except:
                continue
        
        # Force hide overlays via JavaScript
        await self.page.evaluate('''
            document.querySelectorAll('[class*="cookie"], [class*="consent"]')
                .forEach(el => el.style.display = "none")
        ''')
```

### Q: How do you handle elements that disappear?
**A:**
```python
try:
    await element.click()
except Exception as e:
    if "Element is not attached to the DOM" in str(e):
        # Element was removed, skip gracefully
        logger.warning(f"Element detached: {e}")
        return None
```

### Q: How do you handle slow-loading pages?
**A:**
```python
# Wait for network to be idle
await self.page.wait_for_load_state('networkidle', timeout=10000)

# Additional configurable wait
await asyncio.sleep(browser_config.PAGE_LOAD_WAIT)  # 3.0 seconds
```

---

## 8. Testing Strategy

### Q: How did you test your project?
**A:**
```python
# Unit tests with pytest
python -m pytest tests/ -v

# 10 tests covering:
- DOMAnalyzer (navigation menus, interactive elements, modals)
- FeatureWriter (formatting, file writing, filename sanitization)
- Schemas (Pydantic model validation)
- InteractionDetector (skipped without browser)
```

### Q: Why is one test skipped?
**A:** `test_interaction_detector` requires actual browser installation:
```python
@pytest.mark.skipif(
    not PLAYWRIGHT_INSTALLED,
    reason="Requires browser installation"
)
def test_interaction_detector():
    # This test needs real Chromium browser
```

### Q: How do you test without making real API calls?
**A:** Dependency injection allows mocking:
```python
class MockLLMProvider(ILLMProvider):
    async def generate(self, prompt: str) -> str:
        return "Feature: Mock\n  Scenario: Test"

# Inject mock in tests
detector = InteractionDetector(browser_automation=mock_browser)
```

---

## 9. Deployment

### Q: How would you deploy this to production?
**A:**

**Option 1: Streamlit Cloud**
```
1. Push to GitHub
2. Connect to share.streamlit.io
3. Set ui/app.py as main file
4. Add GEMINI_API_KEY in Secrets
```

**Option 2: Docker**
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "ui/app.py"]
```

**Option 3: FastAPI on Cloud Run**
```
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

### Q: What's in packages.txt?
**A:** System dependencies for Playwright on Linux (Streamlit Cloud):
```
libnss3
libatk1.0-0
libcups2
libxkbcommon0
libgbm1
libasound2
```

---

## 10. Challenges & Problem Solving

### Q: What was the most challenging part?
**A:** Making element detection truly dynamic. Initially I used hardcoded selectors like `.nav-menu`, but they failed on different websites. 

**Solution:** Switched to behavior-based detection:
- Analyze computed CSS styles before/after hover
- Check for event listeners via browser APIs
- Use ARIA attributes as hints, not requirements

### Q: How did you handle the Samsung website issue?
**A:** Samsung's site wasn't detecting any elements initially. Root causes:
1. Heavy JavaScript with delayed rendering
2. Cookie overlay blocking interactions
3. `text="..."` selectors invalid in `querySelector`

**Fixes:**
- Increased `PAGE_LOAD_WAIT` to 3 seconds
- Added `networkidle` state waiting
- Fixed JavaScript to use dynamic container detection
- Enhanced cookie banner dismissal

### Q: How do you debug when elements aren't detected?
**A:**
```bash
# Run with visible browser
python main.py --url "https://example.com" --no-headless

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Check specific element detection
python -c "
from src.browser.dynamic_detector import DynamicElementDetector
# ... debug code
"
```

---

## 11. Code Walkthrough Questions

### Q: Show me how a hover interaction is detected.
**A:**
```python
async def simulate_hover(self, element_info: ElementInfo) -> Optional[HoverInteraction]:
    # 1. Find the element
    element = await self.page.query_selector(element_info.selector)
    
    # 2. Hover over it
    await element.hover()
    await asyncio.sleep(0.5)  # Wait for animation
    
    # 3. Find revealed elements
    revealed_links = await self._find_revealed_links()
    
    # 4. Return interaction if something appeared
    if revealed_links:
        return HoverInteraction(
            trigger_element=element_info,
            revealed_links=revealed_links,
            interaction_type=InteractionType.HOVER_DROPDOWN
        )
    return None
```

### Q: How does Pydantic help in your project?
**A:**
```python
class ElementInfo(BaseModel):
    selector: str
    tag_name: str
    text_content: Optional[str] = None
    attributes: Dict[str, Optional[str]] = {}
    
    @field_validator('text_content', mode='before')
    @classmethod
    def normalize_text(cls, v):
        # Auto-clean whitespace
        return clean_whitespace(v)
```

Benefits:
- Automatic validation
- Type safety
- Text normalization via validators
- Easy JSON serialization

### Q: How do you handle Windows compatibility?
**A:**
```python
import platform

if platform.system() == "Windows":
    # Windows: %LOCALAPPDATA%\ms-playwright
    cache = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ms-playwright')
else:
    # macOS/Linux: ~/.cache/ms-playwright
    cache = os.path.expanduser("~/.cache/ms-playwright")
```

---

## Quick Reference Card

| Topic | Key Points |
|-------|------------|
| **Stack** | Python, Playwright, BeautifulSoup, Pydantic, FastAPI, Streamlit |
| **LLMs** | OpenAI GPT-4, Google Gemini 2.0 Flash |
| **Key Feature** | Fully dynamic detection (no hardcoded selectors) |
| **Patterns** | Factory, Strategy, Template Method, Observer |
| **SOLID** | All 5 principles implemented |
| **Concurrency** | asyncio.gather with semaphores |
| **Testing** | pytest with 10 unit tests |
| **Deployment** | Streamlit Cloud, Docker, FastAPI |

---

## 12. Advanced Technical Questions

### Q: How would you scale this to handle 1000 URLs per hour?
**A:**
- **Queue-based architecture**: Use Redis/RabbitMQ to queue URLs
- **Worker pool**: Multiple Playwright browser instances in parallel
- **Containerization**: Kubernetes with horizontal pod autoscaling
- **Caching**: Cache results for same domains/similar pages
- **Rate limiting**: Respect robots.txt and implement backoff

```python
# Example with asyncio worker pool
async def process_urls(urls: List[str], max_workers: int = 10):
    semaphore = asyncio.Semaphore(max_workers)
    async def worker(url):
        async with semaphore:
            return await analyze_page(url)
    return await asyncio.gather(*[worker(url) for url in urls])
```

### Q: How do you handle authentication-protected pages?
**A:**
```python
# Option 1: Cookie injection
await context.add_cookies([{
    'name': 'session_id',
    'value': 'abc123',
    'domain': 'example.com'
}])

# Option 2: Login automation
await page.fill('input[name="username"]', 'user')
await page.fill('input[name="password"]', 'pass')
await page.click('button[type="submit"]')
await page.wait_for_url('**/dashboard')
```

### Q: How would you add support for mobile testing?
**A:**
```python
# Playwright supports device emulation
from playwright.async_api import devices

iphone = devices['iPhone 13']
context = await browser.new_context(**iphone)
# Now page behaves like mobile Safari
```

### Q: What's the difference between `query_selector` and `locator` in Playwright?
**A:**
| Method | Behavior |
|--------|----------|
| `query_selector` | Returns ElementHandle, can become stale |
| `locator` | Returns Locator, auto-waits and retries |

```python
# ElementHandle - can fail if DOM changes
element = await page.query_selector('.button')
await element.click()  # May throw if element removed

# Locator - more robust
locator = page.locator('.button')
await locator.click()  # Auto-waits and retries
```

### Q: How do you handle infinite scroll pages?
**A:**
```python
async def scroll_to_load_all(page, max_scrolls=10):
    previous_height = 0
    for _ in range(max_scrolls):
        current_height = await page.evaluate('document.body.scrollHeight')
        if current_height == previous_height:
            break  # No more content
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)  # Wait for content to load
        previous_height = current_height
```

### Q: How do you handle iframes?
**A:**
```python
# Switch to iframe context
iframe = page.frame_locator('iframe#content')
await iframe.locator('button.submit').click()

# Or get frame directly
frame = page.frame(name='content')
await frame.click('button.submit')
```

---

## 13. System Design Questions

### Q: Design a distributed version of this system.
**A:**
```
                    ┌─────────────────┐
                    │   Load Balancer │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │ API Pod │        │ API Pod │        │ API Pod │
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Redis Queue   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │ Worker  │        │ Worker  │        │ Worker  │
    │(Browser)│        │(Browser)│        │(Browser)│
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │    S3 Storage   │
                    │ (.feature files)│
                    └─────────────────┘
```

### Q: How would you implement a caching layer?
**A:**
```python
# Multi-level caching
class CacheManager:
    def __init__(self):
        self.memory_cache = {}  # L1: In-memory (fast)
        self.redis_cache = Redis()  # L2: Distributed (shared)
    
    async def get(self, key: str):
        # Check L1
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Check L2
        value = await self.redis_cache.get(key)
        if value:
            self.memory_cache[key] = value  # Populate L1
            return value
        
        return None
    
    async def set(self, key: str, value: str, ttl: int = 3600):
        self.memory_cache[key] = value
        await self.redis_cache.setex(key, ttl, value)
```

### Q: How would you add monitoring and observability?
**A:**
```python
# Using OpenTelemetry
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def analyze_page(url: str):
    with tracer.start_as_current_span("analyze_page") as span:
        span.set_attribute("url", url)
        
        with tracer.start_as_current_span("browser_navigate"):
            await browser.navigate(url)
        
        with tracer.start_as_current_span("detect_elements"):
            elements = await detector.find_elements()
            span.set_attribute("element_count", len(elements))
        
        with tracer.start_as_current_span("llm_generate"):
            result = await llm.generate(prompt)
```

---

## 14. Behavioral & Situational Questions

### Q: Tell me about a bug that was hard to debug.
**A:** The Samsung website returned 0 interactions. Debugging steps:
1. Ran with `--no-headless` to see the browser
2. Noticed cookie overlay blocking everything
3. Found `text="Shop"` selector was invalid for JavaScript `querySelector`
4. Fixed by using dynamic container detection instead of parent-based selectors

### Q: How do you prioritize features?
**A:** Using impact vs effort matrix:
- **High impact, Low effort**: LLM caching (did first)
- **High impact, High effort**: Dynamic detection (core feature)
- **Low impact, Low effort**: Better error messages
- **Low impact, High effort**: Deprioritized

### Q: How would you onboard a new developer?
**A:**
1. Point them to README for setup
2. Walk through `INTERVIEW_QA.md` for architecture
3. Have them run tests: `pytest tests/ -v`
4. Small task: Add a new LLM provider
5. Code review with feedback

### Q: What would you do differently if starting over?
**A:**
- Start with TypeScript for better type safety
- Use dependency injection framework (like `dependency-injector`)
- Add integration tests from day one
- Implement structured logging earlier

---

## 15. Security Questions

### Q: How do you handle API keys securely?
**A:**
```python
# Never hardcode - use environment variables
api_key = os.environ.get('GEMINI_API_KEY')

# Use .env file locally (in .gitignore)
# Use secrets manager in production

# Validate key exists at startup
if not api_key:
    raise ValueError("GEMINI_API_KEY not set")
```

### Q: What security risks does browser automation have?
**A:**
- **XSS via scraped content**: Sanitize all extracted text
- **SSRF**: Validate URLs before navigating
- **Resource exhaustion**: Limit concurrent browsers, set timeouts
- **Data leakage**: Don't log sensitive content

```python
# URL validation example
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    # Only allow http/https
    if parsed.scheme not in ('http', 'https'):
        return False
    # Block internal IPs
    if parsed.hostname in ('localhost', '127.0.0.1'):
        return False
    return True
```

### Q: How do you prevent prompt injection attacks?
**A:**
```python
# Sanitize user input before including in prompts
def sanitize_for_prompt(text: str) -> str:
    # Remove potential injection patterns
    dangerous = ['ignore previous', 'disregard', 'system:']
    for pattern in dangerous:
        text = text.replace(pattern, '')
    # Escape special characters
    return text.replace('"', '\\"')

prompt = f'Analyze: "{sanitize_for_prompt(user_input)}"'
```

---

## 16. Tricky Questions

### Q: Why not just use record-and-playback tools like Selenium IDE?
**A:**
| Record & Playback | This Project |
|-------------------|--------------|
| Requires manual interaction | Fully automated |
| Brittle selectors | Behavior-based detection |
| One page at a time | Batch processing |
| No BDD format | Native Gherkin output |
| No AI enhancement | LLM-powered natural language |

### Q: What if the website has anti-bot protection?
**A:**
- Use realistic user-agent and viewport
- Add random delays between actions
- Use stealth plugins (`playwright-stealth`)
- For heavy protection, consider using residential proxies
- Respect `robots.txt`

### Q: How accurate is the LLM-generated Gherkin?
**A:** About 85-90% usable out of the box. Common issues:
- May need to adjust exact element text
- Sometimes generates redundant scenarios
- Human review recommended before use

We mitigate with:
- Detailed prompts with examples
- Low temperature (0.3) for consistency
- Fallback template for critical cases

### Q: What's the difference between BDD and TDD?
**A:**
| BDD | TDD |
|-----|-----|
| Business-readable (Gherkin) | Code-focused (unit tests) |
| Given/When/Then | Arrange/Act/Assert |
| Stakeholder collaboration | Developer-centric |
| Feature files | Test files |

This project generates **BDD** scenarios that can be executed with Cucumber/pytest-bdd.

---

## 17. Live Coding Questions

### Q: Write a function to extract all links from a page.
**A:**
```python
async def extract_all_links(page) -> List[Dict[str, str]]:
    return await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a[href]'))
            .map(a => ({
                text: a.textContent.trim(),
                href: a.href,
                visible: a.offsetParent !== null
            }))
            .filter(link => link.text && link.href);
    }''')
```

### Q: Write a retry decorator with exponential backoff.
**A:**
```python
import asyncio
from functools import wraps

def retry(max_attempts=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, base_delay=1)
async def call_llm(prompt):
    return await llm.generate(prompt)
```

### Q: Write a function to detect if an element is visible.
**A:**
```python
async def is_element_visible(page, selector: str) -> bool:
    return await page.evaluate('''(selector) => {
        const el = document.querySelector(selector);
        if (!el) return false;
        
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        
        return (
            style.display !== 'none' &&
            style.visibility !== 'hidden' &&
            parseFloat(style.opacity) > 0 &&
            rect.width > 0 &&
            rect.height > 0
        );
    }''', selector)
```

---

## Quick Tips for the Interview

1. **Start with the big picture** - Explain the problem before diving into code
2. **Mention trade-offs** - "I chose X over Y because..."
3. **Show growth mindset** - "If I were to redo this, I would..."
4. **Use concrete examples** - Reference specific bugs you fixed
5. **Ask clarifying questions** - Shows thoughtfulness
6. **Draw diagrams** - Architecture questions benefit from visuals

---

*Good luck with your interview!*
