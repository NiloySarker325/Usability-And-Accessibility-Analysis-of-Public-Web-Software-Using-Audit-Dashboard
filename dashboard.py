import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Accessibility Audit Dashboard")
st.title("Section 508 Accessibility Audit")

# --- 1. Data Loading ---
@st.cache_data
def load_data():
    # Read the actual audit results generated from your urls.csv by audit.py
    df = pd.read_csv("audit_results.csv")
    
    # Fallback: Create a 'State' column if the scraper didn't generate one, 
    # defaulting to MN based on the provided urls.csv list.
    if 'State' not in df.columns:
        df['State'] = "MN"
        
    return df

try:
    df = load_data()
    
    # Polish the text columns for cleaner display
    df['Display Impact'] = df['impact'].str.title()
    df['Display Violation'] = df['violation_id'].str.replace('-', ' ').str.title()
    
    # --- 2. State Selection Dropdown & Filtering ---
    st.markdown("### Filter by State")
    state_options = ["All States"] + sorted(df['State'].unique().tolist())
    
    selected_states = st.multiselect(
        "Choose States to Analyze:",
        options=state_options,
        default=["All States"],
        help="Select 'All States', a single state, or multiple states to filter the data."
    )
    
    if "All States" in selected_states or not selected_states:
        filtered_df = df
        display_states = "All States"
    else:
        filtered_df = df[df['State'].isin(selected_states)]
        display_states = ", ".join(selected_states)
        
    st.write(f"**Showing Results for:** {display_states} ({len(filtered_df['url'].unique())} Unique URLs)")
    st.divider()

    # Move the URL filter from the sidebar to the main page to free up horizontal space
    selected_url = st.selectbox("Filter by URL", ["All URLs"] + list(filtered_df['url'].unique()))
    
    if selected_url != "All URLs":
        filtered_df = filtered_df[filtered_df['url'] == selected_url]

    # Adjust column ratio to give the donut chart more horizontal space (1 vs 1.2)
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("Violations by Impact Level")
        impact_counts = filtered_df['Display Impact'].value_counts().reset_index()
        impact_counts.columns = ['Impact', 'Count']
        
        color_map = {'Critical': '#ff4b4b', 'Serious': '#ffa421', 'Moderate': '#ffe115', 'Minor': '#21c354'}
        fig = px.bar(impact_counts, x='Impact', y='Count', color='Impact', color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="Impact = %{x}<br>Count = %{y}<extra></extra>")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Most Frequent Compliance Failures")
        violation_counts = filtered_df['Display Violation'].value_counts().head(10).reset_index()
        violation_counts.columns = ['Violation Type', 'Count']
        
        fig2 = px.pie(violation_counts, names='Violation Type', values='Count', hole=0.4)
        
        fig2.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            textfont_size=14, 
            hovertemplate="Violation Type = %{label}<br>Count = %{value}<extra></extra>"
        )
        fig2.update_layout(height=500, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig2, use_container_width=True)
        
    st.divider()
    
    st.subheader("Actionable HTML Failures")
    st.markdown("Isolate specific violations to extract the exact CSS selector and HTML snippet for remediation.")
    
    selected_violation = st.selectbox("Isolate Violation Type", ["All Violations"] + list(filtered_df['Display Violation'].unique()))
    
    display_df = filtered_df if selected_violation == "All Violations" else filtered_df[filtered_df['Display Violation'] == selected_violation]
    
    st.dataframe(
        display_df[['State', 'Display Impact', 'Display Violation', 'css_selector', 'html_snippet', 'description', 'url']],
        use_container_width=True,
        hide_index=True,
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

except FileNotFoundError:
    st.warning("No audit_results.csv found. Run audit.py first to generate the data.")
except Exception as e:
    st.error(f"An error occurred loading the dashboard: {e}")