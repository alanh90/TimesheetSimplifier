"""
Data models for Timesheet Simplifier
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import uuid


class ChargeCode(BaseModel):
    """Represents a charge code with all its components"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    friendly_name: str
    percent: Optional[float] = None
    task_source: Optional[str] = None
    task: Optional[str] = None
    sub_task: Optional[str] = None
    operating_unit: Optional[str] = None
    process: Optional[str] = None
    project: Optional[str] = None
    activity: Optional[str] = None
    customer_segment: Optional[str] = None
    full_code: Optional[str] = None  # Concatenated code for easy copying
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    def get_display_name(self) -> str:
        """Returns the friendly name for display"""
        return self.friendly_name

    def get_full_code_string(self) -> str:
        """Returns a formatted string of all charge code components"""
        components = []
        if self.percent:
            components.append(f"Percent: {self.percent}")
        if self.task_source:
            components.append(f"Task Source: {self.task_source}")
        if self.task:
            components.append(f"Task: {self.task}")
        if self.sub_task:
            components.append(f"SubTask: {self.sub_task}")
        if self.operating_unit:
            components.append(f"Operating Unit: {self.operating_unit}")
        if self.process:
            components.append(f"Process: {self.process}")
        if self.project:
            components.append(f"Project: {self.project}")
        if self.activity:
            components.append(f"Activity: {self.activity}")
        if self.customer_segment:
            components.append(f"Customer Segment: {self.customer_segment}")

        return " | ".join(components) if components else "No charge code details"


class TimeEntry(BaseModel):
    """Represents a single time entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    charge_code_id: str
    charge_code_name: str  # Store the friendly name for quick reference
    hours: float = Field(gt=0, le=24)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('hours')
    def validate_hours(cls, v):
        if v <= 0:
            raise ValueError('Hours must be greater than 0')
        if v > 24:
            raise ValueError('Hours cannot exceed 24 per entry')
        return v


class DailyEntries(BaseModel):
    """Container for all entries on a specific date"""
    date: date
    entries: List[TimeEntry] = []
    total_hours: float = 0

    def add_entry(self, entry: TimeEntry):
        """Add an entry and update total hours"""
        self.entries.append(entry)
        self.recalculate_total()

    def remove_entry(self, entry_id: str):
        """Remove an entry by ID"""
        self.entries = [e for e in self.entries if e.id != entry_id]
        self.recalculate_total()

    def recalculate_total(self):
        """Recalculate total hours for the day"""
        self.total_hours = sum(e.hours for e in self.entries)

    def validate_total_hours(self, max_hours: float = 24) -> bool:
        """Validate that total hours don't exceed maximum"""
        return self.total_hours <= max_hours


class TimeEntryTemplate(BaseModel):
    """Template for quick entry of common tasks"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    charge_code_id: str
    charge_code_name: str
    default_hours: float = 8.0
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class WeeklySummary(BaseModel):
    """Summary of time entries for a week"""
    week_start: date
    week_end: date
    total_hours: float = 0
    entries_by_charge_code: Dict[str, Dict[str, Any]] = {}
    daily_totals: Dict[str, float] = {}

    def add_daily_entries(self, daily: DailyEntries):
        """Add daily entries to the weekly summary"""
        date_str = daily.date.isoformat()
        self.daily_totals[date_str] = daily.total_hours

        for entry in daily.entries:
            if entry.charge_code_id not in self.entries_by_charge_code:
                self.entries_by_charge_code[entry.charge_code_id] = {
                    'name': entry.charge_code_name,
                    'total_hours': 0,
                    'entries': []
                }

            self.entries_by_charge_code[entry.charge_code_id]['total_hours'] += entry.hours
            self.entries_by_charge_code[entry.charge_code_id]['entries'].append(entry)

        self.recalculate_total()

    def recalculate_total(self):
        """Recalculate total hours for the week"""
        self.total_hours = sum(self.daily_totals.values())