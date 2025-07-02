"""
Test suite for Timesheet Simplifier
Run with: python test_app.py
"""

import unittest
from datetime import date, timedelta
import os
import tempfile
import shutil

# Import our modules
from src.models import ChargeCode, TimeEntry, DailyEntries
from src.utils import ConfigManager, ChargeCodeManager, TimeEntryManager, get_week_dates


class TestModels(unittest.TestCase):
    """Test data models"""

    def test_charge_code_creation(self):
        """Test ChargeCode model creation"""
        cc = ChargeCode(
            friendly_name="Test Project",
            project="PROJ-001",
            task="Development",
            operating_unit="IT"
        )

        self.assertEqual(cc.friendly_name, "Test Project")
        self.assertEqual(cc.project, "PROJ-001")
        self.assertTrue(cc.active)
        self.assertIsNotNone(cc.id)

    def test_charge_code_display_string(self):
        """Test charge code display string generation"""
        cc = ChargeCode(
            friendly_name="Test Project",
            project="PROJ-001",
            task="Development",
            operating_unit="IT",
            percent=100
        )

        display_string = cc.get_full_code_string()
        self.assertIn("Percent: 100", display_string)
        self.assertIn("Project: PROJ-001", display_string)
        self.assertIn("Task: Development", display_string)

    def test_time_entry_validation(self):
        """Test TimeEntry validation"""
        # Valid entry
        entry = TimeEntry(
            date=date.today(),
            charge_code_id="test-id",
            charge_code_name="Test Project",
            hours=8.0
        )
        self.assertEqual(entry.hours, 8.0)

        # Invalid hours (too high)
        with self.assertRaises(ValueError):
            TimeEntry(
                date=date.today(),
                charge_code_id="test-id",
                charge_code_name="Test Project",
                hours=25.0
            )

        # Invalid hours (zero)
        with self.assertRaises(ValueError):
            TimeEntry(
                date=date.today(),
                charge_code_id="test-id",
                charge_code_name="Test Project",
                hours=0
            )

    def test_daily_entries(self):
        """Test DailyEntries functionality"""
        daily = DailyEntries(date=date.today())

        # Add entries
        entry1 = TimeEntry(
            date=date.today(),
            charge_code_id="id1",
            charge_code_name="Project 1",
            hours=4.0
        )
        entry2 = TimeEntry(
            date=date.today(),
            charge_code_id="id2",
            charge_code_name="Project 2",
            hours=4.0
        )

        daily.add_entry(entry1)
        daily.add_entry(entry2)

        self.assertEqual(len(daily.entries), 2)
        self.assertEqual(daily.total_hours, 8.0)
        self.assertTrue(daily.validate_total_hours(24))
        self.assertFalse(daily.validate_total_hours(7))

        # Remove entry
        daily.remove_entry(entry1.id)
        self.assertEqual(len(daily.entries), 1)
        self.assertEqual(daily.total_hours, 4.0)


class TestUtils(unittest.TestCase):
    """Test utility functions"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

        # Create test config
        self.config = ConfigManager()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_config_manager(self):
        """Test ConfigManager"""
        # Test directory creation
        self.assertTrue(os.path.exists(self.config.get('paths.charge_codes_dir')))
        self.assertTrue(os.path.exists(self.config.get('paths.data_dir')))
        self.assertTrue(os.path.exists(self.config.get('paths.export_dir')))

        # Test config retrieval
        self.assertEqual(self.config.get('app.name'), 'Timesheet Simplifier')
        self.assertIsNone(self.config.get('nonexistent.key'))
        self.assertEqual(self.config.get('nonexistent.key', 'default'), 'default')

    def test_time_entry_manager(self):
        """Test TimeEntryManager"""
        tem = TimeEntryManager(self.config)

        # Add entry
        entry = TimeEntry(
            date=date.today(),
            charge_code_id="test-id",
            charge_code_name="Test Project",
            hours=8.0
        )

        self.assertTrue(tem.add_entry(entry))

        # Retrieve entries
        entries = tem.get_entries_for_date(date.today())
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].hours, 8.0)

        # Test daily limit
        entry2 = TimeEntry(
            date=date.today(),
            charge_code_id="test-id",
            charge_code_name="Test Project",
            hours=20.0  # Would exceed 24 hour limit
        )
        self.assertFalse(tem.add_entry(entry2))

        # Delete entry
        self.assertTrue(tem.delete_entry(entry.id, date.today()))
        entries = tem.get_entries_for_date(date.today())
        self.assertEqual(len(entries), 0)

    def test_week_dates(self):
        """Test get_week_dates function"""
        # Test Monday
        monday = date(2025, 1, 6)  # A Monday
        start, end = get_week_dates(monday)
        self.assertEqual(start, monday)
        self.assertEqual(end, date(2025, 1, 12))  # Sunday

        # Test mid-week
        wednesday = date(2025, 1, 8)  # A Wednesday
        start, end = get_week_dates(wednesday)
        self.assertEqual(start, date(2025, 1, 6))  # Monday
        self.assertEqual(end, date(2025, 1, 12))  # Sunday


class TestChargeCodeManager(unittest.TestCase):
    """Test ChargeCodeManager"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

        self.config = ConfigManager()
        self.ccm = ChargeCodeManager(self.config)

        # Create test charge code file
        self.test_file = os.path.join(
            self.config.get('paths.charge_codes_dir'),
            'test_codes.csv'
        )

        with open(self.test_file, 'w') as f:
            f.write('friendly_name,project,task\n')
            f.write('Test Project 1,PROJ-001,Development\n')
            f.write('Test Project 2,PROJ-002,Support\n')

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_find_charge_code_file(self):
        """Test finding charge code file"""
        found_file = self.ccm.find_charge_code_file()
        self.assertIsNotNone(found_file)
        self.assertTrue(found_file.endswith('test_codes.csv'))

    def test_load_charge_codes(self):
        """Test loading charge codes from file"""
        codes = self.ccm.load_charge_codes(self.test_file)
        self.assertEqual(len(codes), 2)
        self.assertEqual(codes[0].friendly_name, 'Test Project 1')
        self.assertEqual(codes[1].project, 'PROJ-002')

    def test_get_charge_code_by_id(self):
        """Test retrieving charge code by ID"""
        self.ccm.load_charge_codes(self.test_file)

        code_id = self.ccm.charge_codes[0].id
        retrieved = self.ccm.get_charge_code_by_id(code_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.friendly_name, 'Test Project 1')

        # Test non-existent ID
        self.assertIsNone(self.ccm.get_charge_code_by_id('non-existent'))


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

        self.config = ConfigManager()
        self.ccm = ChargeCodeManager(self.config)
        self.tem = TimeEntryManager(self.config)

        # Create and load test charge codes
        test_file = os.path.join(
            self.config.get('paths.charge_codes_dir'),
            'test_codes.csv'
        )
        with open(test_file, 'w') as f:
            f.write('friendly_name,project,task\n')
            f.write('Integration Test Project,INT-001,Testing\n')

        self.ccm.load_charge_codes(test_file)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_full_workflow(self):
        """Test complete workflow from entry to export"""
        # Get charge code
        charge_code = self.ccm.charge_codes[0]

        # Create entries for multiple days
        for i in range(5):
            entry_date = date.today() - timedelta(days=i)
            entry = TimeEntry(
                date=entry_date,
                charge_code_id=charge_code.id,
                charge_code_name=charge_code.friendly_name,
                hours=8.0,
                notes=f"Day {i + 1} work"
            )
            self.tem.add_entry(entry)

        # Test weekly summary
        week_start, _ = get_week_dates(date.today())
        summary = self.tem.get_weekly_summary(week_start)

        self.assertGreater(summary.total_hours, 0)
        self.assertIn(charge_code.id, summary.entries_by_charge_code)

        # Test export
        export_file = os.path.join(self.config.get('paths.export_dir'), 'test_export.csv')
        self.tem.export_to_csv(
            date.today() - timedelta(days=7),
            date.today(),
            export_file
        )

        self.assertTrue(os.path.exists(export_file))


def run_tests():
    """Run all tests"""
    print("Running Timesheet Simplifier Tests...")
    print("=" * 50)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestModels))
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestChargeCodeManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()