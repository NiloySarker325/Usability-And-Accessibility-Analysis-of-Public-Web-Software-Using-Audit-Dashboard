Markdown
# Accessibility Audit Dashboard

An automated web accessibility auditing tool that scans public websites for Section 508 and WCAG compliance failures. It utilizes Playwright and Axe-core for headless browser evaluation and provides an interactive Streamlit dashboard to visualize the results, allowing developers to easily isolate and remediate failing HTML nodes.

## Features
* **Automated Scanning:** Headlessly navigates a list of target URLs to evaluate accessibility barriers.
* **Axe-Core Integration:** Detects critical UI/UX flaws including missing ARIA labels, poor color contrast, and invalid heading structures.
* **Actionable Reporting:** Extracts the exact CSS selectors and raw HTML snippets responsible for each violation.
* **Interactive Dashboard:** Visualizes impact levels and most frequent failures using Streamlit and Plotly.

## Prerequisites
* Python 3.8 or higher
* [Git](https://git-scm.com/)

## Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/a11y-audit-dashboard.git](https://github.com/yourusername/a11y-audit-dashboard.git)
   cd a11y-audit-dashboard
Create and activate a virtual environment:

Bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
Install the required dependencies:

Bash
pip install playwright axe-playwright-python pandas plotly streamlit
Install the Playwright browser binaries:

Bash
playwright install chromium
Usage
Configure Target URLs:
Add the websites you want to audit to the urls.csv file in the root directory. Ensure the file has a url header:

Code snippet
url
[https://example.com](https://example.com)
[https://example.org](https://example.org)
Run the Audit:
Execute the scraping script to generate the accessibility report. Depending on the number of URLs, this may take a few minutes.

Bash
python audit.py
This will generate an audit_results.csv file containing the raw violation data.

Launch the Dashboard:
Start the interactive Streamlit application to visualize the findings.

Bash
streamlit run dashboard.py