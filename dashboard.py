import streamlit as st
import pandas as pd
import plotly.express as px
from playwright.sync_api import sync_playwright
from axe_playwright_python.sync_playwright import Axe

st.set_page_config(layout="wide", page_title="Accessibility Audit Dashboard")
st.title("Section 508 Accessibility Audit")

# --- 1. Global State Extraction Logic ---
state_domains = {
    "alabama.gov": "AL", "alaska.gov": "AK", "az.gov": "AZ", "arkansas.gov": "AR",
    "ca.gov": "CA", "colorado.gov": "CO", "ct.gov": "CT", "delaware.gov": "DE",
    "myflorida.com": "FL", "georgia.gov": "GA", "hawaii.gov": "HI", "idaho.gov": "ID",
    "illinois.gov": "IL", "in.gov": "IN", "iowa.gov": "IA", "kansas.gov": "KS",
    "kentucky.gov": "KY", "louisiana.gov": "LA", "maine.gov": "ME", "maryland.gov": "MD",
    "mass.gov": "MA", "michigan.gov": "MI", "mn.gov": "MN", "ms.gov": "MS",
    "mo.gov": "MO", "mt.gov": "MT", "nebraska.gov": "NE", "nv.gov": "NV",
    "nh.gov": "NH", "nj.gov": "NJ", "newmexico.gov": "NM", "ny.gov": "NY",
    "nc.gov": "NC", "nd.gov": "ND", "ohio.gov": "OH", "ok.gov": "OK",
    "oregon.gov": "OR", "pa.gov": "PA", "ri.gov": "RI", "sc.gov": "SC",
    "sd.gov": "SD", "tn.gov": "TN", "texas.gov": "TX", "utah.gov": "UT",
    "vermont.gov": "VT", "virginia.gov": "VA", "wa.gov": "WA", "wv.gov": "WV",
    "wisconsin.gov": "WI", "wyo.gov": "WY"
}

def extract_state(url):
    if pd.isna(url): 
        return "Unknown"
    url_lower = str(url).lower()
    for domain, state in state_domains.items():
        if domain in url_lower:
            return state
    return "Unknown"

# --- 2. Reusable Visuals Function (Don't Repeat Yourself) ---
def render_dashboard_visuals(filtered_df, key_prefix):
    if filtered_df.empty:
        st.info("No compliance violations found for the selected filters (or no data available).")
        return

    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("Violations by Impact Level")
        impact_counts = filtered_df['Display Impact'].value_counts().reset_index()
        impact_counts.columns = ['Impact', 'Count']
        
        color_map = {'Critical': '#ff4b4b', 'Serious': '#ffa421', 'Moderate': '#ffe115', 'Minor': '#21c354'}
        fig = px.bar(impact_counts, x='Impact', y='Count', color='Impact', color_discrete_map=color_map)
        fig.update_traces(hovertemplate="Impact = %{x}<br>Count = %{y}<extra></extra>")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_bar")
        
    with col2:
        st.subheader("Most Frequent Compliance Failures")
        violation_counts = filtered_df['Display Violation'].value_counts().head(10).reset_index()
        violation_counts.columns = ['Violation Type', 'Count']
        
        fig2 = px.pie(violation_counts, names='Violation Type', values='Count', hole=0.4)
        fig2.update_traces(
            textposition='inside', textinfo='percent+label', textfont_size=14, 
            hovertemplate="Violation Type = %{label}<br>Count = %{value}<extra></extra>"
        )
        fig2.update_layout(height=500, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig2, use_container_width=True, key=f"{key_prefix}_pie")
        
    st.divider()
    
    st.subheader("Actionable HTML Failures")
    selected_violation = st.selectbox(
        "Isolate Violation Type", 
        ["All Violations"] + list(filtered_df['Display Violation'].unique()), 
        key=f"{key_prefix}_violation_select"
    )
    
    display_df = filtered_df if selected_violation == "All Violations" else filtered_df[filtered_df['Display Violation'] == selected_violation]
    
    st.dataframe(
        display_df[['State', 'Display Impact', 'Display Violation', 'css_selector', 'html_snippet', 'description', 'url']],
        use_container_width=True, hide_index=True,
        column_config={
            "State": st.column_config.TextColumn("State", width="small"),
            "html_snippet": st.column_config.TextColumn("Failing HTML Snippet", width="large"),
            "css_selector": st.column_config.TextColumn("CSS Target", width="medium"),
            "description": st.column_config.TextColumn("Fix Description", width="medium"),
            "Display Impact": st.column_config.TextColumn("Severity"),
            "Display Violation": st.column_config.TextColumn("Violation Type"),
            "url": st.column_config.TextColumn("URL")
        }
    )

# --- 3. Dashboard Layout & Tabs ---
tab1, tab2 = st.tabs(["Batch Analysis (CSV)", "Individual Live Checker"])

# ==========================================
# TAB 1: BATCH ANALYSIS
# ==========================================
with tab1:
    st.header("Batch CSV Analysis")
    try:
        # Load data once and cache it
        @st.cache_data
        def load_batch_data():
            df = pd.read_csv("audit_results.csv")
            df['State'] = df['url'].apply(extract_state)
            df['Display Impact'] = df['impact'].str.title()
            df['Display Violation'] = df['violation_id'].str.replace('-', ' ').str.title()
            return df
            
        batch_df = load_batch_data()
        
        # State Filter
        state_options = ["All States"] + sorted(batch_df['State'].unique().tolist())
        selected_states = st.multiselect("Choose States to Analyze:", options=state_options, default=["All States"], key="batch_state")
        
        if "All States" in selected_states or not selected_states:
            filtered_batch_df = batch_df
        else:
            filtered_batch_df = batch_df[batch_df['State'].isin(selected_states)]
            
        # URL Filter
        url_options = ["All URLs"] + list(filtered_batch_df['url'].unique())
        selected_urls = st.multiselect("Choose addresses to display:", options=url_options, default=["All URLs"], key="batch_url")
        
        if "All URLs" not in selected_urls and selected_urls:
            filtered_batch_df = filtered_batch_df[filtered_batch_df['url'].isin(selected_urls)]

        # Render charts
        render_dashboard_visuals(filtered_batch_df, key_prefix="batch")

    except FileNotFoundError:
        st.warning("No audit_results.csv found. Run audit.py in the terminal first to generate batch data.")
    except Exception as e:
        st.error(f"An error occurred loading the batch dashboard: {e}")

# ==========================================
# TAB 2: INDIVIDUAL CHECKER
# ==========================================
with tab2:
    st.header("Live Individual Checker")
    st.markdown("Enter URLs manually below to run a live Section 508 accessibility audit.")
    
    # Text area for user input
    url_input = st.text_area("Enter Web Addresses (one per line):", placeholder="https://mn.gov/admin/\nhttps://www.alabama.gov/")
    
    if st.button("Run Live Audit"):
        # Clean up the input string into a list of URLs
        raw_urls = [u.strip() for u in url_input.split('\n') if u.strip()]
        
        if not raw_urls:
            st.error("Please enter at least one URL.")
        else:
            # Show a loading spinner while Playwright runs in the background
            with st.spinner(f'Auditing {len(raw_urls)} URLs in a headless browser... This may take a moment.'):
                live_results = []
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    for url in raw_urls:
                        # Ensure http/https prefix exists so Playwright doesn't crash
                        if not url.startswith("http"):
                            url = "https://" + url
                            
                        try:
                            page.goto(url, timeout=30000)
                            axe = Axe()
                            axe_results = axe.run(page)
                            
                            for violation in axe_results.response.get("violations", []):
                                for node in violation.get("nodes", []):
                                    live_results.append({
                                        "url": url,
                                        "violation_id": violation.get("id"),
                                        "impact": violation.get("impact"),
                                        "description": violation.get("description"),
                                        "css_selector": ", ".join(node.get("target", [])),
                                        "html_snippet": node.get("html")
                                    })
                        except Exception as e:
                            st.warning(f"Failed to audit {url}: {e}")
                    
                    browser.close()
                
                # Save the custom live results into Streamlit's temporary session state
                if live_results:
                    live_df = pd.DataFrame(live_results)
                    live_df['State'] = live_df['url'].apply(extract_state)
                    live_df['Display Impact'] = live_df['impact'].str.title()
                    live_df['Display Violation'] = live_df['violation_id'].str.replace('-', ' ').str.title()
                    st.session_state['live_audit_results'] = live_df
                else:
                    st.success("Audit complete! No accessibility violations found on the entered URLs.")
                    st.session_state['live_audit_results'] = None

    # Render results if they exist in the current session
    if 'live_audit_results' in st.session_state and st.session_state['live_audit_results'] is not None:
        st.success("Live audit complete!")
        live_df = st.session_state['live_audit_results']
        
        st.markdown("### Filter Results")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            # State Filter (Optional)
            live_state_options = ["All States"] + sorted(live_df['State'].unique().tolist())
            selected_live_states = st.multiselect("Filter by State (Optional):", options=live_state_options, default=["All States"], key="live_state")
            
        with col_f2:
            # URL Filter (Multiple Selection)
            live_url_options = ["All URLs"] + list(live_df['url'].unique())
            selected_live_urls = st.multiselect("Choose addresses to display:", options=live_url_options, default=["All URLs"], key="live_url")

        # Apply filters
        filtered_live_df = live_df
        if "All States" not in selected_live_states and selected_live_states:
            filtered_live_df = filtered_live_df[filtered_live_df['State'].isin(selected_live_states)]
            
        if "All URLs" not in selected_live_urls and selected_live_urls:
            filtered_live_df = filtered_live_df[filtered_live_df['url'].isin(selected_live_urls)]

        # Render charts using the reusable function
        render_dashboard_visuals(filtered_live_df, key_prefix="live")