import streamlit as st
import pandas as pd
import plotly.express as px
import re
import urllib.parse
from playwright.sync_api import sync_playwright
from axe_playwright_python.sync_playwright import Axe

st.set_page_config(layout="wide", page_title="Accessibility Audit Dashboard")
st.title("Section 508 Accessibility Audit")

# --- 1. Global State Extraction Logic (UPDATED) ---
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
        
    # 1. Check for full state names in domain (e.g., minnesotastate.edu)
    for name, abbrev in state_map.items():
        if name in domain:
            return abbrev
            
    # 2. Check for .state.xx.us or .xx.us (e.g., state.mn.us or mn.us)
    match_us = re.search(r'\.(state\.)?([a-z]{2})\.us\b', domain)
    if match_us and match_us.group(2).upper() in two_letter_codes:
        return match_us.group(2).upper()
        
    # 3. Check for xx.gov or xx.edu (e.g., mn.gov)
    match_gov = re.search(r'\b([a-z]{2})\.(gov|edu)\b', domain)
    if match_gov and match_gov.group(1).upper() in two_letter_codes:
        return match_gov.group(1).upper()
        
    # 4. Check for xxstate (e.g., mnstate.edu)
    match_xxstate = re.search(r'\b([a-z]{2})state\b', domain)
    if match_xxstate and match_xxstate.group(1).upper() in two_letter_codes:
        return match_xxstate.group(1).upper()
        
    return "Unknown"

# --- 2. Reusable Visuals Function ---
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
        @st.cache_data
        def load_batch_data():
            df = pd.read_csv("audit_results.csv")
            df['State'] = df['url'].apply(extract_state)
            df['Display Impact'] = df['impact'].str.title()
            df['Display Violation'] = df['violation_id'].str.replace('-', ' ').str.title()
            return df
            
        batch_df = load_batch_data()
        
        state_options = ["All States"] + sorted(batch_df['State'].unique().tolist())
        selected_states = st.multiselect("Choose States to Analyze:", options=state_options, default=["All States"], key="batch_state")
        
        if "All States" in selected_states or not selected_states:
            filtered_batch_df = batch_df
        else:
            filtered_batch_df = batch_df[batch_df['State'].isin(selected_states)]
            
        url_options = ["All URLs"] + list(filtered_batch_df['url'].unique())
        selected_urls = st.multiselect("Choose addresses to display:", options=url_options, default=["All URLs"], key="batch_url")
        
        if "All URLs" not in selected_urls and selected_urls:
            filtered_batch_df = filtered_batch_df[filtered_batch_df['url'].isin(selected_urls)]

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
    
    url_input = st.text_area("Enter Web Addresses (one per line):", placeholder="https://www.mda.state.mn.us/\nhttps://www.alabama.gov/")
    
    if st.button("Run Live Audit"):
        raw_urls = [u.strip() for u in url_input.split('\n') if u.strip()]
        
        if not raw_urls:
            st.error("Please enter at least one URL.")
        else:
            with st.spinner(f'Auditing {len(raw_urls)} URLs in a headless browser... This may take a moment.'):
                live_results = []
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    for url in raw_urls:
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
                
                if live_results:
                    live_df = pd.DataFrame(live_results)
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