"""
Timesheet Simplifier - Main Streamlit Application
A modern time tracking solution that simplifies complex charge code management
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
import os
from pathlib import Path
import json

from src.models import TimeEntry, ChargeCode, WeeklySummary
from src.utils import ConfigManager, ChargeCodeManager, TimeEntryManager, get_week_dates, format_hours

# Page configuration
st.set_page_config(
    page_title="Timesheet Simplifier",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = ConfigManager()

if 'charge_code_manager' not in st.session_state:
    st.session_state.charge_code_manager = ChargeCodeManager(st.session_state.config)

if 'time_entry_manager' not in st.session_state:
    st.session_state.time_entry_manager = TimeEntryManager(st.session_state.config)

# Shortcuts for managers
config = st.session_state.config
cc_manager = st.session_state.charge_code_manager
te_manager = st.session_state.time_entry_manager

# Enhanced Professional CSS for Modern Dark Theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables */
    :root {
        --primary-color: #6366F1;
        --primary-hover: #5558E3;
        --secondary-color: #10B981;
        --secondary-hover: #059669;
        --accent-color: #F59E0B;
        --error-color: #EF4444;
        --warning-color: #F59E0B;
        --success-color: #10B981;
        --bg-primary: #0F172A;
        --bg-secondary: #1E293B;
        --bg-tertiary: #334155;
        --text-primary: #F1F5F9;
        --text-secondary: #CBD5E1;
        --text-muted: #94A3B8;
        --border-color: #334155;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        --radius-sm: 0.375rem;
        --radius-md: 0.5rem;
        --radius-lg: 0.75rem;
    }
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        letter-spacing: -0.025em;
        color: var(--text-primary);
    }
    
    h1 {
        font-size: 2.25rem;
        line-height: 2.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--border-color);
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        font-size: 1.875rem;
        line-height: 2.25rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }
    
    h3 {
        font-size: 1.5rem;
        line-height: 2rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        color: var(--text-secondary);
    }
    
    /* Containers and Cards */
    .stContainer > div > div {
        background: var(--bg-secondary);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }
    
    .stContainer > div > div:hover {
        box-shadow: var(--shadow-lg);
        border-color: var(--primary-color);
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--primary-color);
    }
    
    [data-testid="metric-container"] > div > div:first-child {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="metric-container"] > div > div:nth-child(2) {
        color: var(--text-primary);
        font-size: 2rem;
        font-weight: 700;
        margin-top: 0.25rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
        color: white;
        border: none;
        padding: 0.625rem 1.25rem;
        border-radius: var(--radius-md);
        font-weight: 500;
        font-size: 0.875rem;
        letter-spacing: 0.025em;
        transition: all 0.2s ease;
        cursor: pointer;
        box-shadow: var(--shadow-sm);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.2);
        transition: left 0.3s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Form Elements */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        border-radius: var(--radius-md);
        padding: 0.625rem 0.875rem;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stDateInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        outline: none;
    }
    
    /* Labels */
    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stDateInput > label,
    .stTextArea > label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar */
    .css-1d391kg, .stSidebar > div {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    .stSidebar .stRadio > label {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 1rem;
        margin-bottom: 1rem;
    }
    
    .stSidebar .stRadio > div > label {
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: var(--radius-md);
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .stSidebar .stRadio > div > label:hover {
        background: var(--bg-tertiary);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary);
        border-radius: var(--radius-lg);
        padding: 0.25rem;
        gap: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: var(--radius-md);
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-color) !important;
        color: white !important;
        box-shadow: var(--shadow-sm);
    }
    
    /* Tables */
    .dataframe {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
        font-size: 0.875rem;
    }
    
    .dataframe thead th {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 0.75rem 1rem;
        text-align: left;
        border-bottom: 2px solid var(--border-color);
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    
    .dataframe tbody td {
        padding: 0.75rem 1rem;
        color: var(--text-secondary);
        border-bottom: 1px solid var(--border-color);
    }
    
    .dataframe tbody tr:hover {
        background: var(--bg-tertiary);
    }
    
    .dataframe tbody tr:last-child td {
        border-bottom: none;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 0.875rem 1.25rem;
        font-weight: 500;
        color: var(--text-primary);
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--bg-tertiary);
        border-color: var(--primary-color);
    }
    
    .streamlit-expanderContent {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 var(--radius-md) var(--radius-md);
        padding: 1.25rem;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.875rem;
    }
    
    /* Success/Error/Warning/Info Messages */
    .stAlert {
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        border-width: 1px;
        font-size: 0.875rem;
    }
    
    .stAlert[data-baseweb="notification"][kind="info"] {
        background: rgba(99, 102, 241, 0.1);
        border-color: var(--primary-color);
        color: var(--text-primary);
    }
    
    .stAlert[data-baseweb="notification"][kind="success"] {
        background: rgba(16, 185, 129, 0.1);
        border-color: var(--success-color);
        color: var(--text-primary);
    }
    
    .stAlert[data-baseweb="notification"][kind="warning"] {
        background: rgba(245, 158, 11, 0.1);
        border-color: var(--warning-color);
        color: var(--text-primary);
    }
    
    .stAlert[data-baseweb="notification"][kind="error"] {
        background: rgba(239, 68, 68, 0.1);
        border-color: var(--error-color);
        color: var(--text-primary);
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
        overflow: hidden;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    }
    
    /* Download button special styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--secondary-color), var(--secondary-hover));
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, var(--secondary-hover), var(--secondary-color));
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-color);
    }
    
    /* Plotly charts dark theme override */
    .js-plotly-plot .plotly {
        background: var(--bg-secondary) !important;
    }
    
    /* Custom utility classes */
    .gradient-text {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function"""

    # Header with improved branding
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.markdown('<div style="font-size: 3rem;">⏰</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<h1 class="gradient-text">Timesheet Simplifier</h1>', unsafe_allow_html=True)
        org_name = config.get('app.organization', 'Your Organization')
        team_name = config.get('app.team', 'Your Team')
        st.markdown(f'<p style="color: var(--text-secondary); font-size: 1rem; margin-top: -1rem;">{org_name} • {team_name} • Making time tracking simple and efficient</p>', unsafe_allow_html=True)
    with col3:
        # Add current date/time
        st.markdown(f'<div style="text-align: right; color: var(--text-muted); font-size: 0.875rem;">{datetime.now().strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)

    # Check for charge codes file
    charge_code_file = cc_manager.find_charge_code_file()
    if not charge_code_file:
        show_no_charge_codes_warning()
        return

    # Load charge codes
    cc_manager.refresh_if_needed()
    if not cc_manager.charge_codes:
        st.error("❌ No valid charge codes found in the file. Please check the file format.")
        with st.expander("📋 View Required File Format", expanded=True):
            show_file_format_tab()
        return

    # Sidebar for navigation
    with st.sidebar:
        st.markdown('<h2 style="color: var(--primary-color); margin-bottom: 1.5rem;">🧭 Navigation</h2>', unsafe_allow_html=True)

        page = st.radio(
            "Choose a section:",
            ["📝 Time Entry", "📊 Dashboard", "📅 History", "📤 Export", "📋 File Format", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Quick Stats Card
        st.markdown('<h3 style="color: var(--text-secondary); font-size: 1.125rem; margin-bottom: 1rem;">📈 Quick Stats</h3>', unsafe_allow_html=True)

        today_entries = te_manager.get_daily_entries(date.today())
        week_start, week_end = get_week_dates(date.today())
        weekly_summary = te_manager.get_weekly_summary(week_start)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Today", format_hours(today_entries.total_hours) + " hrs",
                     delta=f"{8 - today_entries.total_hours:.1f} remaining" if today_entries.total_hours < 8 else "Complete ✓")
        with col2:
            st.metric("This Week", format_hours(weekly_summary.total_hours) + " hrs",
                     delta=f"{40 - weekly_summary.total_hours:.1f} remaining" if weekly_summary.total_hours < 40 else f"+{weekly_summary.total_hours - 40:.1f} overtime")

        # Recent Activity
        st.markdown("---")
        st.markdown('<h3 style="color: var(--text-secondary); font-size: 1.125rem; margin-bottom: 1rem;">🕐 Recent Activity</h3>', unsafe_allow_html=True)

        recent_entries = te_manager.get_entries_for_range(date.today() - timedelta(days=3), date.today())
        recent_entries.sort(key=lambda x: x.created_at, reverse=True)

        if recent_entries[:3]:
            for entry in recent_entries[:3]:
                st.markdown(f"""
                <div style="padding: 0.5rem; margin-bottom: 0.5rem; background: var(--bg-tertiary); border-radius: var(--radius-sm);">
                    <div style="font-weight: 500; color: var(--text-primary); font-size: 0.813rem;">{entry.charge_code_name}</div>
                    <div style="color: var(--text-muted); font-size: 0.75rem;">{entry.date.strftime('%b %d')} • {format_hours(entry.hours)} hrs</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent entries")

    # Main content area
    if page == "📝 Time Entry":
        show_time_entry_page()
    elif page == "📊 Dashboard":
        show_dashboard_page()
    elif page == "📅 History":
        show_history_page()
    elif page == "📤 Export":
        show_export_page()
    elif page == "📋 File Format":
        show_file_format_tab()
    elif page == "⚙️ Settings":
        show_settings_page()


def show_no_charge_codes_warning():
    """Display warning when no charge codes file is found"""
    st.markdown("""
    <div style="background: var(--bg-secondary); border: 2px solid var(--warning-color); border-radius: var(--radius-lg); padding: 2rem; margin: 2rem 0;">
        <h2 style="color: var(--warning-color); margin-bottom: 1rem;">⚠️ No Charge Code File Found</h2>
        <p style="color: var(--text-primary); margin-bottom: 1.5rem;">
            To get started, please ask your manager to provide a charge code file and place it in the <code>charge_codes</code> directory.
        </p>
        <h3 style="color: var(--text-secondary); margin-bottom: 0.5rem;">📁 Accepted File Formats:</h3>
        <ul style="color: var(--text-secondary);">
            <li>Excel files (.xlsx, .xls)</li>
            <li>CSV files (.csv)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 View Required File Format", expanded=True):
        show_file_format_tab()


def show_file_format_tab():
    """Show the charge code file format requirements"""
    st.markdown("## 📋 Charge Code File Format")

    st.markdown("""
    <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 2rem;">
        <h3 style="color: var(--primary-color); margin-bottom: 1rem;">📝 File Requirements</h3>
        <p style="color: var(--text-primary);">
            Your charge code file should be in Excel (.xlsx, .xls) or CSV format with the following structure:
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Required and optional columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: var(--bg-secondary); border-radius: var(--radius-md); padding: 1.25rem;">
            <h4 style="color: var(--success-color);">✅ Required Column</h4>
            <ul style="color: var(--text-secondary);">
                <li><strong>friendly_name</strong> - The display name for the charge code</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: var(--bg-secondary); border-radius: var(--radius-md); padding: 1.25rem;">
            <h4 style="color: var(--primary-color);">📊 Optional Columns</h4>
            <ul style="color: var(--text-secondary); font-size: 0.875rem;">
                <li>percent</li>
                <li>task_source</li>
                <li>task</li>
                <li>sub_task</li>
                <li>operating_unit</li>
                <li>process</li>
                <li>project</li>
                <li>activity</li>
                <li>customer_segment</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Sample data
    st.markdown("### 📄 Sample File Content")

    sample_df = pd.DataFrame({
        'friendly_name': [
            'Web Development - Phase 1',
            'Mobile App Enhancement',
            'Data Analytics Platform',
            'Infrastructure Maintenance',
            'Security Compliance Review'
        ],
        'percent': [100, 100, 100, 100, 100],
        'task_source': ['IT', 'IT', 'IT', 'IT', 'IT'],
        'task': ['Development', 'Development', 'Development', 'Operations', 'Security'],
        'sub_task': ['Frontend', 'Mobile', 'Analytics', 'Maintenance', 'Audit'],
        'operating_unit': ['Technology', 'Technology', 'Technology', 'Technology', 'Technology'],
        'process': ['Software Development', 'Software Development', 'Business Intelligence', 'Infrastructure', 'Security'],
        'project': ['WEB-2025-001', 'MOB-2025-017', 'DAT-2025-003', 'INF-2025-M01', 'SEC-2025-A12'],
        'activity': ['Implementation', 'Enhancement', 'Development', 'Maintenance', 'Compliance'],
        'customer_segment': ['Internal', 'External', 'Internal', 'Internal', 'Internal']
    })

    st.dataframe(sample_df, use_container_width=True, height=250)

    # Download sample file
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        csv = sample_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Sample CSV File",
            data=csv,
            file_name="sample_charge_codes.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Instructions
    st.markdown("""
    <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1.5rem; margin-top: 2rem;">
        <h3 style="color: var(--primary-color); margin-bottom: 1rem;">📚 Instructions</h3>
        <ol style="color: var(--text-secondary); line-height: 1.8;">
            <li>Download the sample file above as a template</li>
            <li>Replace the sample data with your organization's charge codes</li>
            <li>Ensure each charge code has a unique, descriptive <strong>friendly_name</strong></li>
            <li>Fill in the applicable columns for your organization's accounting structure</li>
            <li>Save the file and place it in the <code>charge_codes</code> directory</li>
            <li>Restart the application or click "Refresh Charge Codes" in Settings</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # Tips
    with st.expander("💡 Pro Tips", expanded=False):
        st.markdown("""
        - **Friendly Names**: Use clear, descriptive names that your team will recognize
        - **Consistency**: Keep naming conventions consistent across projects
        - **Updates**: When charge codes change, simply update the file and refresh
        - **Multiple Files**: The app will use the most recently modified file in the directory
        - **Validation**: The app will skip any rows without a friendly_name
        """)


def show_time_entry_page():
    """Enhanced time entry page"""
    st.markdown("## 📝 Daily Time Entry")

    # Quick entry buttons for common dates
    st.markdown("### 🗓️ Quick Date Selection")
    col1, col2, col3, col4, col5 = st.columns(5)

    quick_dates = {
        "Today": date.today(),
        "Yesterday": date.today() - timedelta(days=1),
        "Monday": date.today() - timedelta(days=date.today().weekday()),
        "Last Friday": date.today() - timedelta(days=(date.today().weekday() + 3) % 7 if date.today().weekday() < 5 else 0),
        "Custom": None
    }

    selected_quick_date = "Today"
    for i, (label, date_val) in enumerate(quick_dates.items()):
        col = [col1, col2, col3, col4, col5][i]
        with col:
            if st.button(label, key=f"quick_date_{label}", use_container_width=True):
                selected_quick_date = label
                if date_val:
                    st.session_state['selected_date'] = date_val

    # Date selection
    col1, col2 = st.columns([2, 3])
    with col1:
        if 'selected_date' not in st.session_state:
            st.session_state['selected_date'] = date.today()

        selected_date = st.date_input(
            "Select Date",
            value=st.session_state['selected_date'],
            max_value=date.today(),
            help="Choose the date for your time entry"
        )
        st.session_state['selected_date'] = selected_date

    #