import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / 'battery.sqlite'
        self.patch = patch.object(database, 'DB_PATH', str(self.db_path))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp_dir.cleanup()

    def test_schema_and_sample_round_trip(self):
        database.init_db()
        database.record_battery_sample(
            percent=72, is_charging=False, time_remaining_sec=3600,
            power_watts=14.2, voltage_v=12.4, cpu_temp_c=None,
            gpu_temp_c=None, cpu_fan_rpm=None, gpu_fan_rpm=None
        )
        rows = database.get_recent_samples(hours=24)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['percent'], 72.0)
        self.assertEqual(rows[0]['power_watts'], 14.2)

    def test_charge_cycle_round_trip(self):
        database.init_db()
        database.record_charge_cycle('2026-11-20T10:00:00', 95, 42, '2026-11-20T13:00:00')
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute('SELECT start_percent, end_percent FROM charge_cycles').fetchone()
        finally:
            conn.close()
        self.assertEqual(row, (95.0, 42.0))


if __name__ == '__main__':
    unittest.main()
