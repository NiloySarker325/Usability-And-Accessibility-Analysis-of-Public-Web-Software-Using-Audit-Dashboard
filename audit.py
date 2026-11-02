import pandas as pd
from playwright.sync_api import sync_playwright
from axe_playwright_python.sync_playwright import Axe
from tqdm import tqdm  # Import the progress bar library

def run_audit():
    df = pd.read_csv("urls.csv")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Wrap the loop with tqdm to generate the live progress bar
        for url in tqdm(df['url'], desc="Auditing URLs", unit="site"):
            try:
                page.goto(url, timeout=30000)
                axe = Axe()
                axe_results = axe.run(page)
                
                for violation in axe_results.response.get("violations", []):
                    for node in violation.get("nodes", []):
                        results.append({
                            "url": url,
                            "violation_id": violation.get("id"),
                            "impact": violation.get("impact"),
                            "description": violation.get("description"),
                            "css_selector": ", ".join(node.get("target", [])),
                            "html_snippet": node.get("html")
                        })
            except Exception as e:
                # Use tqdm.write instead of standard print so it doesn't break the visual progress bar
                tqdm.write(f"Failed to audit {url}: {e}")

        browser.close()

    results_df = pd.DataFrame(results)
    results_df.to_csv("audit_results.csv", index=False)
    print("\nAudit complete. Data saved to audit_results.csv")

if __name__ == "__main__":
    run_audit()