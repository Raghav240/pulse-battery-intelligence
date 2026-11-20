import sqlite3
import os
import sys
import datetime
from contextlib import contextmanager

if getattr(sys, 'frozen', False):
    DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.dirname(sys.executable)), 'WindowsBatteryStats')
else:
    DATA_DIR = os.path.dirname(__file__)

os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'battery_stats.db')

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS battery_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                percent REAL NOT NULL,
                is_charging INTEGER NOT NULL,
                charge_mwh INTEGER,
                capacity_mwh INTEGER,
                time_remaining_sec INTEGER,
                power_watts REAL,
                voltage_v REAL,
                cpu_temp_c REAL,
                gpu_temp_c REAL,
                cpu_fan_rpm INTEGER,
                gpu_fan_rpm INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                app_name TEXT NOT NULL,
                exe_path TEXT,
                active_seconds INTEGER DEFAULT 0,
                background_seconds INTEGER DEFAULT 0,
                cpu_seconds REAL DEFAULT 0.0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS charge_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unplugged_at TEXT NOT NULL,
                start_percent REAL NOT NULL,
                end_percent REAL,
                plugged_at TEXT,
                total_screen_on_sec INTEGER DEFAULT 0,
                total_screen_off_sec INTEGER DEFAULT 0
            )
        ''')
        # Keep existing installations compatible while allowing richer samples.
        existing = {row[1] for row in cursor.execute('PRAGMA table_info(battery_samples)').fetchall()}
        for name, sql_type in {
            'power_watts': 'REAL', 'voltage_v': 'REAL', 'cpu_temp_c': 'REAL',
            'gpu_temp_c': 'REAL', 'cpu_fan_rpm': 'INTEGER', 'gpu_fan_rpm': 'INTEGER'
        }.items():
            if name not in existing:
                cursor.execute(f'ALTER TABLE battery_samples ADD COLUMN {name} {sql_type}')
        conn.commit()

def record_battery_sample(percent, is_charging, charge_mwh=None, capacity_mwh=None,
                          time_remaining_sec=None, power_watts=None, voltage_v=None,
                          cpu_temp_c=None, gpu_temp_c=None, cpu_fan_rpm=None,
                          gpu_fan_rpm=None, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute('''
            INSERT INTO battery_samples (
                timestamp, percent, is_charging, charge_mwh, capacity_mwh,
                time_remaining_sec, power_watts, voltage_v, cpu_temp_c,
                gpu_temp_c, cpu_fan_rpm, gpu_fan_rpm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, percent, 1 if is_charging else 0, charge_mwh, capacity_mwh,
              time_remaining_sec, power_watts, voltage_v, cpu_temp_c, gpu_temp_c,
              cpu_fan_rpm, gpu_fan_rpm))
        conn.commit()

def record_charge_cycle(unplugged_at, start_percent, end_percent=None, plugged_at=None,
                        total_screen_on_sec=0, total_screen_off_sec=0):
    with get_connection() as conn:
        conn.execute('''
            INSERT INTO charge_cycles
            (unplugged_at, start_percent, end_percent, plugged_at,
             total_screen_on_sec, total_screen_off_sec)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (unplugged_at, start_percent, end_percent, plugged_at,
              total_screen_on_sec, total_screen_off_sec))
        conn.commit()

def record_app_activity(app_name, exe_path, active_sec, background_sec=0, cpu_sec=0.0):
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:00')
    with get_connection() as conn:
        # Check if row exists for this minute and app
        row = conn.execute('''
            SELECT id, active_seconds, background_seconds, cpu_seconds FROM app_sessions
            WHERE timestamp = ? AND app_name = ?
        ''', (now_str, app_name)).fetchone()
        if row:
            conn.execute('''
                UPDATE app_sessions
                SET active_seconds = active_seconds + ?,
                    background_seconds = background_seconds + ?,
                    cpu_seconds = cpu_seconds + ?
                WHERE id = ?
            ''', (active_sec, background_sec, cpu_sec, row['id']))
        else:
            conn.execute('''
                INSERT INTO app_sessions (timestamp, app_name, exe_path, active_seconds, background_seconds, cpu_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (now_str, app_name, exe_path, active_sec, background_sec, cpu_sec))
        conn.commit()

def get_recent_samples(hours=24):
    since = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat()
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT timestamp, percent, is_charging, charge_mwh, capacity_mwh,
                   time_remaining_sec, power_watts, voltage_v, cpu_temp_c,
                   gpu_temp_c, cpu_fan_rpm, gpu_fan_rpm
            FROM battery_samples
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        ''', (since,)).fetchall()
        return [dict(r) for r in rows]

if __name__ == '__main__':
    init_db()
    print("Database initialized at", DB_PATH)
