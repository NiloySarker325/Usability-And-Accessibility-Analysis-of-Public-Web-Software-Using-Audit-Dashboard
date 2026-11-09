Section 508 Web Accessibility Audit Dashboard

An automated, high-velocity accessibility auditing tool and interactive dashboard designed to evaluate public sector web infrastructure (U.S. State and Municipal websites) for Section 504 and Section 508 compliance against WCAG 2.1 AA standards.

📖 Project Overview

Equal access to digital government services is a fundamental civil right. However, widespread usability barriers continue to marginalize users with disabilities. This project provides a scalable architecture to programmatically scan, diagnose, and visualize web accessibility failures across thousands of domains.

By combining the speed of Playwright headless browser automation with the precision of the Axe-core rules engine, this tool shifts accessibility testing "left." It bridges the gap between compliance monitoring and remediation by providing developers with the exact CSS selectors, failing HTML snippets, and plain-English fix descriptions needed to resolve issues.

✨ Key Features

Batch CSV Analysis: Analyze pre-computed audit results of 2,500+ state agency URLs.

Drag-and-Drop Auditing: Upload your own CSV of URLs directly into the dashboard to run a live batch audit with a real-time progress bar.

Live Individual Checker: Manually enter specific URLs to execute on-the-fly accessibility audits in a headless Chromium browser without leaving the dashboard.

Intelligent State Routing: Automatically parses domain structures (e.g., .gov, .edu, .state.xx.us) to assign and filter data by U.S. State.

Actionable Remediation Table: Isolates specific HTML failures, providing the exact CSS Target and HTML Snippet to fix structural (e.g., missing ARIA landmarks) and visual (e.g., color contrast) errors.

🗂 File Structure

generate_urls.py: Generates a synthetic dataset (urls.csv) of 2,500 standardized U.S. state and municipal web addresses.

audit.py: The backend batch-processing script. Reads urls.csv, launches a headless browser, runs the Axe-core engine, and outputs violations to audit_results.csv with a live terminal progress bar.

dashboard.py: The interactive Streamlit frontend for data visualization and live URL checking.

🚀 Installation & Setup

It is highly recommended to run this project inside a Python Virtual Environment to isolate the required dependencies.

1. Clone the repository and create a virtual environment

git clone https://github.com/yourusername/accessibility-audit-dashboard.git
cd accessibility-audit-dashboard
python -m venv .venv


2. Activate the virtual environment

Windows: .venv\Scripts\activate

Mac/Linux: source .venv/bin/activate

3. Install Python dependencies

pip install streamlit pandas plotly playwright axe-playwright-python tqdm


4. Install Playwright Browser Binaries (Crucial Step)

Because the audit requires a real browser engine to render dynamic JavaScript content before testing, you must install the Playwright Chromium binaries:

playwright install chromium


💻 Usage Instructions

Option A: Run the Pre-Computed Dashboard

If you already have an audit_results.csv file, you can instantly launch the interactive dashboard:

streamlit run dashboard.py


Option B: Run a Full Batch Audit from Scratch

If you want to generate a fresh dataset and run a massive batch audit from your terminal:

Generate Target URLs:

python generate_urls.py


(This creates urls.csv)

Execute the Audit:

python audit.py


(This will take time. The terminal will display a live tqdm progress bar as it processes sites and outputs to audit_results.csv)

Launch the Dashboard:

streamlit run dashboard.py


🔮 Future Work

Future iterations of this project intend to integrate Predictive Machine Learning (Logistic Regression & XGBoost). By engineering features from the HTML metadata and domain types, we aim to predict the likelihood of critical accessibility failures and use SHAP (SHapley Additive exPlanations) values to interpret model feature importance directly within the Streamlit UI.

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.