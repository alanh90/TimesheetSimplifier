"""
Utility functions for Timesheet Simplifier
"""
import os
import json
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import toml
import glob
from models import ChargeCode, TimeEntry, DailyEntries, WeeklySummary


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_path: str = "config.toml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.ensure_directories()

    def load_config(self) -> dict:
        """Load configuration from TOML file"""
        if os.path.exists(self.config_path):
            return toml.load(self.config_path)
        else:
            # Return default config if file doesn't exist
            return {
                "app": {
                    "name": "Timesheet Simplifier",
                    "version": "1.0.0",
                    "organization": "Your Organization",
                    "team": "Your Team"
                },
                "paths": {
                    "charge_codes_dir": "./charge_codes",
                    "data_dir": "./data",
                    "export_dir": "./exports"
                },
                "files": {
                    "charge_code_patterns": ["*.xlsx", "*.xls", "*.csv"],
                    "time_entries_file": "time_entries.json"
                }
            }

    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.config['paths']['charge_codes_dir'],
            self.config['paths']['data_dir'],
            self.config['paths']['export_dir']
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class ChargeCodeManager:
    """Manages charge codes from files"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.charge_codes: List[ChargeCode] = []
        self.last_modified = None

    def find_charge_code_file(self) -> Optional[str]:
        """Find the most recent charge code file"""
        charge_codes_dir = self.config.get('paths.charge_codes_dir')
        patterns = self.config.get('files.charge_code_patterns', ['*.xlsx', '*.xls', '*.csv'])

        all_files = []
        for pattern in patterns:
            files = glob.glob(os.path.join(charge_codes_dir, pattern))
            all_files.extend(files)

        if not all_files:
            return None

        # Return the most recently modified file
        return max(all_files, key=os.path.getmtime)

    def load_charge_codes(self, file_path: str) -> List[ChargeCode]:
        """Load charge codes from file"""
        if not os.path.exists(file_path):
            return []

        file_ext = Path(file_path).suffix.lower()

        if file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        charge_codes = []

        # Expected columns mapping
        column_mapping = {
            'friendly_name': ['friendly_name', 'name', 'project_name', 'task_name'],
            'percent': ['percent', 'percentage', '%'],
            'task_source': ['task_source', 'task source', 'source'],
            'task': ['task'],
            'sub_task': ['sub_task', 'subtask', 'sub task'],
            'operating_unit': ['operating_unit', 'operating unit', 'unit'],
            'process': ['process'],
            'project': ['project', 'project_code'],
            'activity': ['activity'],
            'customer_segment': ['customer_segment', 'customer segment', 'segment']
        }

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        for _, row in df.iterrows():
            charge_code_data = {}

            # Map columns
            for field, possible_names in column_mapping.items():
                for col_name in possible_names:
                    if col_name in df.columns and pd.notna(row.get(col_name)):
                        charge_code_data[field] = str(row[col_name]).strip()
                        break

            # Skip if no friendly name
            if 'friendly_name' not in charge_code_data:
                continue

            charge_codes.append(ChargeCode(**charge_code_data))

        self.charge_codes = charge_codes
        self.last_modified = os.path.getmtime(file_path)
        return charge_codes

    def refresh_if_needed(self) -> bool:
        """Check if charge codes file has been updated and reload if necessary"""
        file_path = self.find_charge_code_file()
        if not file_path:
            return False

        current_modified = os.path.getmtime(file_path)
        if self.last_modified is None or current_modified > self.last_modified:
            self.load_charge_codes(file_path)
            return True
        return False

    def get_charge_code_by_id(self, charge_code_id: str) -> Optional[ChargeCode]:
        """Get a charge code by ID"""
        for cc in self.charge_codes:
            if cc.id == charge_code_id:
                return cc
        return None

    def get_charge_codes_for_dropdown(self) -> List[Tuple[str, str]]:
        """Get charge codes formatted for Streamlit dropdown"""
        return [(cc.id, cc.friendly_name) for cc in self.charge_codes if cc.active]


class TimeEntryManager:
    """Manages time entries"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.entries_file = os.path.join(
            config.get('paths.data_dir'),
            config.get('files.time_entries_file', 'time_entries.json')
        )
        self.entries: Dict[str, List[TimeEntry]] = self.load_entries()

    def load_entries(self) -> Dict[str, List[TimeEntry]]:
        """Load time entries from JSON file"""
        if not os.path.exists(self.entries_file):
            return {}

        try:
            with open(self.entries_file, 'r') as f:
                data = json.load(f)

            entries = {}
            for date_str, entry_list in data.items():
                entries[date_str] = [TimeEntry(**entry) for entry in entry_list]
            return entries
        except Exception as e:
            print(f"Error loading entries: {e}")
            return {}

    def save_entries(self):
        """Save time entries to JSON file"""
        data = {}
        for date_str, entry_list in self.entries.items():
            data[date_str] = [entry.dict() for entry in entry_list]

        with open(self.entries_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def add_entry(self, entry: TimeEntry) -> bool:
        """Add a new time entry"""
        date_str = entry.date.isoformat()

        if date_str not in self.entries:
            self.entries[date_str] = []

        # Check if adding this entry would exceed daily limit
        total_hours = sum(e.hours for e in self.entries[date_str]) + entry.hours
        max_hours = self.config.get('features.max_hours_per_day', 24)

        if total_hours > max_hours:
            return False

        self.entries[date_str].append(entry)
        self.save_entries()
        return True

    def get_entries_for_date(self, date: date) -> List[TimeEntry]:
        """Get all entries for a specific date"""
        date_str = date.isoformat()
        return self.entries.get(date_str, [])

    def get_daily_entries(self, date: date) -> DailyEntries:
        """Get daily entries object for a specific date"""
        entries = self.get_entries_for_date(date)
        daily = DailyEntries(date=date, entries=entries)
        daily.recalculate_total()
        return daily

    def delete_entry(self, entry_id: str, date: date) -> bool:
        """Delete a time entry"""
        date_str = date.isoformat()
        if date_str in self.entries:
            self.entries[date_str] = [e for e in self.entries[date_str] if e.id != entry_id]
            self.save_entries()
            return True
        return False

    def get_entries_for_range(self, start_date: date, end_date: date) -> List[TimeEntry]:
        """Get all entries within a date range"""
        entries = []
        current_date = start_date

        while current_date <= end_date:
            entries.extend(self.get_entries_for_date(current_date))
            current_date += timedelta(days=1)

        return entries

    def get_weekly_summary(self, week_start: date) -> WeeklySummary:
        """Get weekly summary starting from a specific date"""
        week_end = week_start + timedelta(days=6)
        summary = WeeklySummary(week_start=week_start, week_end=week_end)

        current_date = week_start
        while current_date <= week_end:
            daily = self.get_daily_entries(current_date)
            if daily.entries:
                summary.add_daily_entries(daily)
            current_date += timedelta(days=1)

        return summary

    def export_to_csv(self, start_date: date, end_date: date, file_path: str):
        """Export entries to CSV"""
        entries = self.get_entries_for_range(start_date, end_date)

        data = []
        for entry in entries:
            data.append({
                'Date': entry.date,
                'Charge Code': entry.charge_code_name,
                'Hours': entry.hours,
                'Notes': entry.notes or '',
                'Created At': entry.created_at
            })

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)

    def export_to_excel(self, start_date: date, end_date: date, file_path: str, charge_code_manager: ChargeCodeManager):
        """Export entries to Excel with charge code details"""
        entries = self.get_entries_for_range(start_date, end_date)

        data = []
        for entry in entries:
            charge_code = charge_code_manager.get_charge_code_by_id(entry.charge_code_id)

            row = {
                'Date': entry.date,
                'Friendly Name': entry.charge_code_name,
                'Hours': entry.hours,
                'Notes': entry.notes or ''
            }

            if charge_code:
                row.update({
                    'Percent': charge_code.percent,
                    'Task Source': charge_code.task_source,
                    'Task': charge_code.task,
                    'SubTask': charge_code.sub_task,
                    'Operating Unit': charge_code.operating_unit,
                    'Process': charge_code.process,
                    'Project': charge_code.project,
                    'Activity': charge_code.activity,
                    'Customer Segment': charge_code.customer_segment
                })

            data.append(row)

        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, sheet_name='Time Entries')


def get_week_dates(date: date) -> Tuple[date, date]:
    """Get the start and end dates of the week containing the given date"""
    # Assuming week starts on Monday
    days_since_monday = date.weekday()
    week_start = date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def format_hours(hours: float) -> str:
    """Format hours for display"""
    if hours == int(hours):
        return f"{int(hours)}"
    return f"{hours:.1f}"