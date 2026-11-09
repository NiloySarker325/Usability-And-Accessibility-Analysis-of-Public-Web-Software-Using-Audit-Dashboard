import streamlit as st
import pandas as pd
import plotly.express as px
import re
import urllib.parse
from playwright.sync_api import sync_playwright
from axe_playwright_python.sync_playwright import Axe

st.set_page_config(layout="wide", page_title="Accessibility Audit Dashboard")
st.title("Section 508 Accessibility Audit")

# --- 1. Global State Extraction Logic ---
state_map = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "newhampshire": "NH", "newjersey": "NJ", "newmexico": "NM", "newyork": "NY",
    "northcarolina": "NC", "northdakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhodeisland": "RI", "southcarolina": "SC",
    "southdakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "westvirginia": "WV",
    "wisconsin": "WI", "wyoming": "WY"
}

two_letter_codes = set(state_map.values())

def extract_state(url):
    if pd.isna(url): return "Unknown"
    
    try:
        domain = urllib.parse.urlparse(str(url).lower()).netloc
        if not domain:
            domain = str(url).lower()
    except:
        domain = str(url).lower()
        
    for name, abbrev in state_map.items():
        if name in domain: return abbrev
            
    match_us = re.search(r'\.(state\.)?([a-z]{2})\.us\b', domain)
    if match_us and match_us.group(2).upper() in two_letter_codes: return match_us.group(2).upper()
        
    match_gov = re.search(r'\b([a-z]{2})\.(gov|edu)\b', domain)
    if match_gov and match_gov.group(1).upper() in two_letter_codes: return match_gov.group(1).upper()
        
    match_xxstate = re.search(r'\b([a-z]{2})state\b', domain)
    if match_xxstate and match_xxstate.group(1).upper() in two_letter_codes: return match_xxstate.group(1).upper()
        
    return "Unknown"

# --- 2. Centralized Playwright Audit Engine ---
def perform_live_audit(urls):
    """Runs a live Axe audit on a list of URLs with a Streamlit progress bar."""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, url in enumerate(urls):
            if not str(url).startswith("http"):
                url = "https://" + str(url)
                
            status_text.text(f"Auditing ({i+1}/{len(urls)}): {url}")
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
                pass # Skip dead links gracefully
            
            progress_bar.progress((i + 1) / len(urls))
            
        browser.close()
        status_text.empty()
        progress_bar.empty()
        
    return results

# --- 3. Reusable Visuals Function ---
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

# --- 4. Dashboard Layout & Tabs ---
tab1, tab2 = st.tabs(["Batch Analysis (CSV)", "Individual Live Checker"])

# ==========================================
# TAB 1: BATCH ANALYSIS
# ==========================================
with tab1:
    st.header("Batch CSV Analysis")
    st.info("This audit is currently running on the pre-computed results from the automated 'audit_results.csv'. If you want, you can drag and drop your own URL CSV below to run a fresh audit!")
    
    # Drag and Drop File Uploader
    uploaded_file = st.file_uploader("Upload your own CSV file (must contain a 'url' column):", type=["csv"])
    
    display_batch_df = None
    
    # Logic for Uploaded CSV
    if uploaded_file is not None:
        upload_df = pd.read_csv(uploaded_file)
        if 'url' not in upload_df.columns:
            st.error("Error: The uploaded CSV must contain a column named 'url'.")
        else:
            st.success(f"Successfully loaded {len(upload_df)} URLs from your CSV.")
            if st.button("Run Audit on Uploaded CSV"):
                raw_urls = upload_df['url'].dropna().tolist()
                results = perform_live_audit(raw_urls)
                
                if results:
                    res_df = pd.DataFrame(results)
                    res_df['State'] = res_df['url'].apply(extract_state)
                    res_df['Display Impact'] = res_df['impact'].str.title()
                    res_df['Display Violation'] = res_df['violation_id'].str.replace('-', ' ').str.title()
                    st.session_state['uploaded_batch_results'] = res_df
                else:
                    st.session_state['uploaded_batch_results'] = "EMPTY"
                    st.success("Audit complete! No violations found.")
                    
        # Load results from session state if they exist
        if 'uploaded_batch_results' in st.session_state:
            if isinstance(st.session_state['uploaded_batch_results'], pd.DataFrame):
                display_batch_df = st.session_state['uploaded_batch_results']
            
    # Logic for Default Pre-Computed CSV (if no file is uploaded)
    else:
        try:
            @st.cache_data
            def load_batch_data():
                df = pd.read_csv("audit_results.csv")
                df['State'] = df['url'].apply(extract_state)
                df['Display Impact'] = df['impact'].str.title()
                df['Display Violation'] = df['violation_id'].str.replace('-', ' ').str.title()
                return df
                
            display_batch_df = load_batch_data()
        except FileNotFoundError:
            st.warning("No default audit_results.csv found. Run audit.py in the terminal or upload a custom CSV above.")

    # Render Filters and Charts for Tab 1
    if display_batch_df is not None and not display_batch_df.empty:
        st.markdown("### Filter Results")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            state_options = ["All States"] + sorted(display_batch_df['State'].unique().tolist())
            selected_states = st.multiselect("Choose States to Analyze:", options=state_options, default=["All States"], key="batch_state")
            
        with col_f2:
            url_options = ["All URLs"] + list(display_batch_df['url'].unique())
            selected_urls = st.multiselect("Choose addresses to display:", options=url_options, default=["All URLs"], key="batch_url")

        filtered_batch_df = display_batch_df
        if "All States" not in selected_states and selected_states:
            filtered_batch_df = filtered_batch_df[filtered_batch_df['State'].isin(selected_states)]
            
        if "All URLs" not in selected_urls and selected_urls:
            filtered_batch_df = filtered_batch_df[filtered_batch_df['url'].isin(selected_urls)]

        render_dashboard_visuals(filtered_batch_df, key_prefix="batch")


# ==========================================
# TAB 2: INDIVIDUAL CHECKER
# ==========================================
with tab2:
    st.header("Live Individual Checker")
    st.markdown("Enter URLs manually below to run a live Section 508 accessibility audit.")
    
    url_input = st.text_area("Enter Web Addresses (one per line):", placeholder="https://www.mda.state.mn.us/\nhttps://www.alabama.gov/")
    
    if st.button("Run Live Audit"):
        raw_urls = [u.strip() for u in url_input.split('\n') if u.strip()]
        
        if not raw_urls:
            st.error("Please enter at least one URL.")
        else:
            results = perform_live_audit(raw_urls)
            
            if results:
                live_df = pd.DataFrame(results)
                live_df['State'] = live_df['url'].apply(extract_state)
                live_df['Display Impact'] = live_df['impact'].str.title()
                live_df['Display Violation'] = live_df['violation_id'].str.replace('-', ' ').str.title()
                st.session_state['live_audit_results'] = live_df
            else:
                st.success("Audit complete! No accessibility violations found on the entered URLs.")
                st.session_state['live_audit_results'] = None

    if 'live_audit_results' in st.session_state and st.session_state['live_audit_results'] is not None:
        st.success("Live audit complete!")
        live_df = st.session_state['live_audit_results']
        
        st.markdown("### Filter Results")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            live_state_options = ["All States"] + sorted(live_df['State'].unique().tolist())
            selected_live_states = st.multiselect("Filter by State (Optional):", options=live_state_options, default=["All States"], key="live_state")
            
        with col_f2:
            live_url_options = ["All URLs"] + list(live_df['url'].unique())
            selected_live_urls = st.multiselect("Choose addresses to display:", options=live_url_options, default=["All URLs"], key="live_url")

        filtered_live_df = live_df
        if "All States" not in selected_live_states and selected_live_states:
            filtered_live_df = filtered_live_df[filtered_live_df['State'].isin(selected_live_states)]
            
        if "All URLs" not in selected_live_urls and selected_live_urls:
            filtered_live_df = filtered_live_df[filtered_live_df['url'].isin(selected_live_urls)]

        render_dashboard_visuals(filtered_live_df, key_prefix="live")