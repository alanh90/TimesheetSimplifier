"""
Timesheet Simplifier - Main Streamlit Application
A modern time tracking solution that simplifies complex charge code management
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import List, Optional
import os
from pathlib import Path

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

# Dynamic CSS based on config
primary_color = config.get('ui.primary_color', '#1f77b4')
secondary_color = config.get('ui.secondary_color', '#ff7f0e')

# Custom CSS for modern UI
st.markdown(f"""
<style>
    /* Main container */
    .main {{
        padding: 1rem;
    }}

    /* Headers */
    h1 {{
        color: {primary_color};
        font-weight: 700;
        border-bottom: 3px solid {secondary_color};
        padding-bottom: 10px;
        margin-bottom: 30px;
    }}

    h2 {{
        color: {primary_color};
        font-weight: 600;
        margin-top: 30px;
        margin-bottom: 20px;
    }}

    h3 {{
        color: {secondary_color};
        font-weight: 500;
    }}

    /* Cards and containers */
    .stContainer {{
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}

    /* Metrics */
    [data-testid="metric-container"] {{
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {secondary_color};
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 500;
        transition: all 0.3s;
    }}

    .stButton > button:hover {{
        background-color: {primary_color};
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}

    /* Success/Error messages */
    .success-message {{
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }}

    .error-message {{
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }}

    /* Tables */
    .dataframe {{
        font-size: 14px;
    }}

    .dataframe th {{
        background-color: {primary_color} !important;
        color: white !important;
        font-weight: 600;
    }}

    .dataframe tr:nth-child(even) {{
        background-color: #f8f9fa;
    }}

    /* Sidebar */
    .css-1d391kg {{
        background-color: #f0f2f6;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: #e9ecef;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {primary_color};
        color: white;
    }}
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function"""

    # Header with logo/branding
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("# ⏰")
    with col2:
        st.markdown("# Timesheet Simplifier")
        org_name = config.get('app.organization', 'Your Organization')
        team_name = config.get('app.team', 'Your Team')
        st.markdown(f"**{org_name} - {team_name}** | Making time tracking simple and efficient")

    # Check for charge codes file
    charge_code_file = cc_manager.find_charge_code_file()
    if not charge_code_file:
        st.warning("""
        ⚠️ **No charge code file found!**

        Please ask your manager to place a charge code file in the `charge_codes` directory.
        The file should be in Excel (.xlsx, .xls) or CSV format with columns for:
        - Friendly Name (required)
        - Percent, Task Source, Task, SubTask, Operating Unit, Process, Project, Activity, Customer Segment (optional)
        """)

        # Show sample format
        with st.expander("📋 See sample charge code file format"):
            sample_df = pd.DataFrame({
                'friendly_name': ['Project Alpha Development', 'Customer Support - Tier 2',
                                  'Training - Python Advanced'],
                'project': ['PROJ-001', 'SUPP-002', 'TRAIN-003'],
                'task': ['Development', 'Support', 'Training'],
                'operating_unit': ['IT', 'Customer Service', 'HR'],
                'percent': [100, 100, 100]
            })
            st.dataframe(sample_df)
        return

    # Load charge codes
    cc_manager.refresh_if_needed()
    if not cc_manager.charge_codes:
        st.error("No valid charge codes found in the file. Please check the file format.")
        return

    # Sidebar for navigation
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        page = st.radio(
            "Choose a section:",
            ["📝 Time Entry", "📊 Dashboard", "📅 History", "📤 Export", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        today_entries = te_manager.get_daily_entries(date.today())
        st.metric("Today's Hours", format_hours(today_entries.total_hours))

        week_start, week_end = get_week_dates(date.today())
        weekly_summary = te_manager.get_weekly_summary(week_start)
        st.metric("This Week's Hours", format_hours(weekly_summary.total_hours))

    # Main content area
    if page == "📝 Time Entry":
        show_time_entry_page()
    elif page == "📊 Dashboard":
        show_dashboard_page()
    elif page == "📅 History":
        show_history_page()
    elif page == "📤 Export":
        show_export_page()
    elif page == "⚙️ Settings":
        show_settings_page()


def show_time_entry_page():
    """Time entry page"""
    st.markdown("## 📝 Daily Time Entry")

    # Date selection
    col1, col2 = st.columns([2, 3])
    with col1:
        selected_date = st.date_input(
            "Select Date",
            value=date.today(),
            max_value=date.today(),
            help="Choose the date for your time entry"
        )

    # Show existing entries for the selected date
    daily_entries = te_manager.get_daily_entries(selected_date)

    with col2:
        st.markdown(
            f"### Total Hours: {format_hours(daily_entries.total_hours)} / {config.get('features.max_hours_per_day', 24)}")
        if daily_entries.total_hours >= config.get('features.max_hours_per_day', 24):
            st.warning("⚠️ Maximum daily hours reached!")

    # New entry form
    st.markdown("### ➕ Add New Entry")

    with st.form("time_entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 1, 2])

        with col1:
            # Get charge codes for dropdown
            charge_codes = cc_manager.get_charge_codes_for_dropdown()
            if not charge_codes:
                st.error("No charge codes available")
                return

            # Create a mapping for the selectbox
            charge_code_options = {cc[1]: cc[0] for cc in charge_codes}
            selected_charge_code_name = st.selectbox(
                "What did you work on?",
                options=list(charge_code_options.keys()),
                help="Select the project or task you worked on"
            )
            selected_charge_code_id = charge_code_options[selected_charge_code_name]

        with col2:
            hours = st.number_input(
                "Hours",
                min_value=0.5,
                max_value=24.0,
                value=float(config.get('features.default_hours', 8)),
                step=0.5,
                help="Enter the number of hours worked"
            )

        with col3:
            notes = st.text_area(
                "Notes (optional)",
                height=70,
                help="Add any additional notes or details"
            )

        submitted = st.form_submit_button("➕ Add Entry", use_container_width=True)

        if submitted:
            # Create new entry
            new_entry = TimeEntry(
                date=selected_date,
                charge_code_id=selected_charge_code_id,
                charge_code_name=selected_charge_code_name,
                hours=hours,
                notes=notes if notes else None
            )

            # Try to add entry
            if te_manager.add_entry(new_entry):
                st.success("✅ Time entry added successfully!")
                st.rerun()
            else:
                st.error("❌ Cannot add entry - would exceed daily hour limit!")

    # Display existing entries
    if daily_entries.entries:
        st.markdown("### 📋 Today's Entries")

        for i, entry in enumerate(daily_entries.entries):
            charge_code = cc_manager.get_charge_code_by_id(entry.charge_code_id)

            with st.expander(f"{entry.charge_code_name} - {format_hours(entry.hours)} hours", expanded=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"**Hours:** {format_hours(entry.hours)}")
                    if entry.notes:
                        st.markdown(f"**Notes:** {entry.notes}")

                    if charge_code:
                        st.markdown("**Charge Code Details:**")
                        st.code(charge_code.get_full_code_string(), language=None)

                    st.markdown(f"*Added: {entry.created_at.strftime('%I:%M %p')}*")

                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{entry.id}"):
                        te_manager.delete_entry(entry.id, selected_date)
                        st.rerun()


def show_dashboard_page():
    """Dashboard page with visualizations"""
    st.markdown("## 📊 Time Tracking Dashboard")

    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=date.today())

    # Get entries for the range
    entries = te_manager.get_entries_for_range(start_date, end_date)

    if not entries:
        st.info("No entries found for the selected date range.")
        return

    # Prepare data for visualizations
    df = pd.DataFrame([
        {
            'Date': entry.date,
            'Charge Code': entry.charge_code_name,
            'Hours': entry.hours,
            'Day': entry.date.strftime('%A'),
            'Week': entry.date.strftime('%Y-W%U')
        }
        for entry in entries
    ])

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Hours", format_hours(df['Hours'].sum()))
    with col2:
        st.metric("Total Days", df['Date'].nunique())
    with col3:
        st.metric("Avg Hours/Day", format_hours(df['Hours'].sum() / df['Date'].nunique()))
    with col4:
        st.metric("Projects", df['Charge Code'].nunique())

    # Visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Daily Trends", "🥧 Project Distribution", "📅 Weekly Summary", "🔥 Heatmap"])

    with tab1:
        # Daily hours trend
        daily_hours = df.groupby('Date')['Hours'].sum().reset_index()
        fig = px.line(
            daily_hours,
            x='Date',
            y='Hours',
            title='Daily Hours Trend',
            markers=True
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Hours",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Project distribution pie chart
        project_hours = df.groupby('Charge Code')['Hours'].sum().reset_index()
        fig = px.pie(
            project_hours,
            values='Hours',
            names='Charge Code',
            title='Hours by Project/Task'
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Weekly summary
        weekly_hours = df.groupby(['Week', 'Charge Code'])['Hours'].sum().reset_index()
        fig = px.bar(
            weekly_hours,
            x='Week',
            y='Hours',
            color='Charge Code',
            title='Weekly Hours by Project',
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        # Heatmap of hours by day and project
        pivot_df = df.pivot_table(
            values='Hours',
            index='Charge Code',
            columns=df['Date'].dt.strftime('%Y-%m-%d'),
            fill_value=0
        )

        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='Blues',
            hoverongaps=False
        ))
        fig.update_layout(
            title='Hours Heatmap by Project and Date',
            xaxis_title='Date',
            yaxis_title='Project/Task'
        )
        st.plotly_chart(fig, use_container_width=True)


def show_history_page():
    """History page with detailed entry listing"""
    st.markdown("## 📅 Time Entry History")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        filter_start = st.date_input("From Date", value=date.today() - timedelta(days=14))

    with col2:
        filter_end = st.date_input("To Date", value=date.today())

    with col3:
        filter_project = st.selectbox(
            "Filter by Project",
            options=["All"] + [cc.friendly_name for cc in cc_manager.charge_codes]
        )

    # Get entries
    entries = te_manager.get_entries_for_range(filter_start, filter_end)

    # Apply project filter
    if filter_project != "All":
        entries = [e for e in entries if e.charge_code_name == filter_project]

    # Sort by date descending
    entries.sort(key=lambda x: (x.date, x.created_at), reverse=True)

    if not entries:
        st.info("No entries found for the selected criteria.")
        return

    # Display entries grouped by date
    current_date = None
    for entry in entries:
        if entry.date != current_date:
            current_date = entry.date
            st.markdown(f"### {current_date.strftime('%A, %B %d, %Y')}")
            daily_total = sum(e.hours for e in entries if e.date == current_date)
            st.markdown(f"*Daily Total: {format_hours(daily_total)} hours*")

        charge_code = cc_manager.get_charge_code_by_id(entry.charge_code_id)

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 3, 1])

            with col1:
                st.markdown(f"**{entry.charge_code_name}**")

            with col2:
                st.markdown(f"{format_hours(entry.hours)} hrs")

            with col3:
                if entry.notes:
                    st.markdown(f"*{entry.notes}*")

            with col4:
                if st.button("View Details", key=f"view_{entry.id}"):
                    with st.expander("Charge Code Details", expanded=True):
                        if charge_code:
                            st.code(charge_code.get_full_code_string(), language=None)
                        st.markdown(f"*Entry created: {entry.created_at.strftime('%Y-%m-%d %I:%M %p')}*")

            st.markdown("---")


def show_export_page():
    """Export page for downloading data"""
    st.markdown("## 📤 Export Time Entries")

    st.markdown("""
    Export your time entries for use in timesheets or reporting.
    Choose your date range and format below.
    """)

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        export_start = st.date_input("Start Date", value=date.today() - timedelta(days=14))

    with col2:
        export_end = st.date_input("End Date", value=date.today())

    # Format selection
    export_format = st.radio(
        "Export Format",
        ["Excel (.xlsx) - Detailed with charge codes", "CSV - Simple format", "Weekly Summary Report"],
        help="Excel includes all charge code details, CSV is a simple format"
    )

    # Preview
    if st.button("👁️ Preview Export"):
        entries = te_manager.get_entries_for_range(export_start, export_end)

        if not entries:
            st.warning("No entries found for the selected date range.")
        else:
            st.markdown("### Preview (first 10 entries)")

            preview_data = []
            for i, entry in enumerate(entries[:10]):
                charge_code = cc_manager.get_charge_code_by_id(entry.charge_code_id)
                preview_data.append({
                    'Date': entry.date,
                    'Project/Task': entry.charge_code_name,
                    'Hours': entry.hours,
                    'Notes': entry.notes or '-',
                    'Charge Code': charge_code.get_full_code_string() if charge_code else 'N/A'
                })

            st.dataframe(pd.DataFrame(preview_data))
            st.markdown(f"*Total entries: {len(entries)}*")

    # Export button
    if st.button("📥 Download Export", type="primary"):
        entries = te_manager.get_entries_for_range(export_start, export_end)

        if not entries:
            st.error("No entries to export!")
        else:
            export_dir = config.get('paths.export_dir')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if export_format.startswith("Excel"):
                filename = f"time_entries_{timestamp}.xlsx"
                filepath = os.path.join(export_dir, filename)
                te_manager.export_to_excel(export_start, export_end, filepath, cc_manager)

                with open(filepath, 'rb') as f:
                    st.download_button(
                        label="📥 Download Excel File",
                        data=f.read(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            elif export_format.startswith("CSV"):
                filename = f"time_entries_{timestamp}.csv"
                filepath = os.path.join(export_dir, filename)
                te_manager.export_to_csv(export_start, export_end, filepath)

                with open(filepath, 'rb') as f:
                    st.download_button(
                        label="📥 Download CSV File",
                        data=f.read(),
                        file_name=filename,
                        mime="text/csv"
                    )

            elif export_format.startswith("Weekly Summary"):
                # Generate weekly summary report
                st.markdown("### Weekly Summary Report")

                current_date = export_start
                report_data = []

                while current_date <= export_end:
                    week_start, week_end = get_week_dates(current_date)
                    if week_start >= export_start:
                        summary = te_manager.get_weekly_summary(week_start)

                        st.markdown(f"#### Week of {week_start.strftime('%B %d, %Y')}")
                        st.markdown(f"**Total Hours:** {format_hours(summary.total_hours)}")

                        for cc_id, cc_data in summary.entries_by_charge_code.items():
                            st.markdown(f"- **{cc_data['name']}**: {format_hours(cc_data['total_hours'])} hours")

                        st.markdown("---")

                    current_date = week_end + timedelta(days=1)

            st.success("✅ Export completed successfully!")


def show_settings_page():
    """Settings page"""
    st.markdown("## ⚙️ Settings & Information")

    # App info
    st.markdown("### 📱 Application Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Version:** {config.get('app.version', '1.0.0')}")
        st.markdown(f"**Organization:** {config.get('app.organization', 'Your Organization')}")
    with col2:
        st.markdown(f"**Team:** {config.get('app.team', 'Your Team')}")
        st.markdown(f"**Python Version:** 3.10+")

    # File locations
    st.markdown("### 📁 File Locations")
    st.info(f"""
    - **Charge Codes Directory:** `{config.get('paths.charge_codes_dir')}`
    - **Data Directory:** `{config.get('paths.data_dir')}`
    - **Export Directory:** `{config.get('paths.export_dir')}`
    """)

    # Current charge codes
    st.markdown("### 📋 Current Charge Codes")
    if cc_manager.charge_codes:
        charge_code_file = cc_manager.find_charge_code_file()
        st.markdown(f"*Loaded from: {Path(charge_code_file).name}*")

        cc_df = pd.DataFrame([
            {
                'Friendly Name': cc.friendly_name,
                'Project': cc.project or '-',
                'Task': cc.task or '-',
                'Operating Unit': cc.operating_unit or '-',
                'Active': '✅' if cc.active else '❌'
            }
            for cc in cc_manager.charge_codes
        ])
        st.dataframe(cc_df, use_container_width=True)
    else:
        st.warning("No charge codes loaded")

    # Configuration editor
    st.markdown("### 🎨 Customize Appearance")
    with st.expander("Edit Configuration"):
        st.info("Edit `config.toml` to customize your organization name, team, and colors.")
        st.code("""
[app]
organization = "Your Organization Name"
team = "Your Team Name"

[ui]
primary_color = "#1f77b4"  # Main color
secondary_color = "#ff7f0e"  # Accent color
        """, language="toml")

    # Data management
    st.markdown("### 🗄️ Data Management")

    col1, col2 = st.columns(2)
    with col1:
        total_entries = sum(len(entries) for entries in te_manager.entries.values())
        st.metric("Total Time Entries", total_entries)

    with col2:
        if st.button("🔄 Refresh Charge Codes"):
            if cc_manager.refresh_if_needed():
                st.success("✅ Charge codes refreshed!")
            else:
                st.info("ℹ️ Charge codes are already up to date")

    st.markdown("### 🧽 Clear All Data")
    st.warning(
        "⚠️ **Warning: This action is irreversible!** All your recorded time entries will be permanently deleted.")

    if st.button("🚨 Clear All Time Entries", type="secondary", use_container_width=True):
        st.session_state['confirm_clear_data'] = True

    if st.session_state.get('confirm_clear_data', False):
        st.info("Are you sure you want to delete ALL time entries? This cannot be undone.")
        col_confirm1, col_confirm2 = st.columns([1, 4])
        with col_confirm1:
            if st.button("Yes, Delete All", type="primary"):
                if te_manager.clear_all_entries():
                    st.success("✅ All time entries have been cleared successfully!")
                    st.session_state['confirm_clear_data'] = False  # Reset confirmation
                    st.rerun()  # Refresh the app to show cleared state
                else:
                    st.error("❌ Failed to clear time entries. Please check permissions.")
                    st.session_state['confirm_clear_data'] = False  # Reset confirmation
        with col_confirm2:
            if st.button("No, Cancel"):
                st.info("Data deletion cancelled.")
                st.session_state['confirm_clear_data'] = False  # Reset confirmation
                st.rerun()  # Refresh to hide confirmation prompt

    # Help section
    st.markdown("### ❓ Help & Tips")
    with st.expander("How to use this app"):
        st.markdown("""
        1. **Daily Entry**: Go to the Time Entry page and log your hours each day
        2. **Select Project**: Choose from the friendly names in the dropdown
        3. **Enter Hours**: Input the hours worked (0.5 hour increments)
        4. **Add Notes**: Optionally add notes for additional context
        5. **Review History**: Check your entries in the History page
        6. **Export Data**: Use the Export page to download your entries for timesheet submission

        **Tips:**
        - Log your time daily to avoid forgetting details
        - Use notes to capture specific tasks or accomplishments
        - Export your data before each timesheet submission period
        - The charge code details are automatically tracked - you never need to remember them!
        """)

    # About
    st.markdown("### 📖 About")
    st.markdown("""
    **Timesheet Simplifier** transforms complex charge code management into a simple, 
    user-friendly experience. Built with Python and Streamlit, it helps teams track 
    time efficiently without memorizing complicated codes.

    [View on GitHub](https://github.com/alanh90/TimesheetSimplifier)
    """)


if __name__ == "__main__":
    main()