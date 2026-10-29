import pandas as pd
from playwright.sync_api import sync_playwright
from axe_playwright_python.sync_playwright import Axe

def run_audit():
    df = pd.read_csv("urls.csv")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in df['url']:
            try:
                page.goto(url, timeout=30000)
                axe = Axe()
                axe_results = axe.run(page)
                
                # Access the raw JSON response dictionary
                for violation in axe_results.response.get("violations", []):
                    # Iterate through the specific elements causing the failure
                    for node in violation.get("nodes", []):
                        results.append({
                            "url": url,
                            "violation_id": violation.get("id"),
                            "impact": violation.get("impact"),
                            "description": violation.get("description"),
                            # Join the CSS selectors if there are multiple, or return empty string
                            "css_selector": ", ".join(node.get("target", [])),
                            "html_snippet": node.get("html")
                        })
            except Exception as e:
                print(f"Failed to audit {url}: {e}")

        browser.close()

    results_df = pd.DataFrame(results)
    results_df.to_csv("audit_results.csv", index=False)
    print("Audit complete. Data saved to audit_results.csv")

if __name__ == "__main__":
    run_audit()