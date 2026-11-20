import ctypes
import ctypes.wintypes
import subprocess
import tempfile
# -*- coding: utf-8 -*-
import os
import glob
import json
import xml.etree.ElementTree as ET
import datetime
import time
import winreg

class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', ctypes.c_byte),
        ('BatteryFlag', ctypes.c_byte),
        ('BatteryLifePercent', ctypes.c_byte),
        ('SystemStatusFlag', ctypes.c_byte),
        ('BatteryLifeTime', ctypes.c_ulong),
        ('BatteryFullLifeTime', ctypes.c_ulong)
    ]

_cached_report_time = 0
_cached_report_path = os.path.join(tempfile.gettempdir(), 'win_battery_report.xml')

def get_energy_saver_status():
    # Check true Windows Energy Saver / Battery Saver active state via Win32 kernel
    try:
        status = SYSTEM_POWER_STATUS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            # SystemStatusFlag == 1 indicates battery saver is actively engaged
            return status.SystemStatusFlag == 1
    except Exception:
        pass
    return False

def get_active_power_scheme():
    try:
        res = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True, creationflags=0x08000000 if os.name == 'nt' else 0, timeout=2)
        out = res.stdout
        if '(' in out and ')' in out:
            return out.split('(')[-1].split(')')[0].strip()
    except:
        pass
    return 'Balanced'

def get_live_power_status():
    status = SYSTEM_POWER_STATUS()
    success = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
    if not success:
        return {
            'percent': 100,
            'is_charging': False,
            'ac_connected': True,
            'has_battery': True,
            'time_remaining_sec': 0,
            'power_watts': 0.0,
            'voltage_v': 0.0
        }
    
    # Flag 128 means no system battery (Desktop PC)
    has_battery = not bool(status.BatteryFlag & 128)
    ac = status.ACLineStatus == 1
    pct = status.BatteryLifePercent
    
    # 255 means battery status is unknown or no battery
    if pct > 100 or not has_battery:
        pct = 100
        has_battery = False
    
    # 0xFFFFFFFF means unknown or on AC
    life_time = status.BatteryLifeTime
    if life_time == 0xFFFFFFFF or life_time == 4294967295:
        life_time = -1
        
    is_charging = bool(status.BatteryFlag & 8) or (ac and pct < 100 and has_battery)

    # Query WMI for live wattage and voltage
    power_watts = 0.0
    voltage_v = 0.0
    try:
        cmd = 'Get-CimInstance -Namespace root\\wmi -ClassName BatteryStatus | Select-Object DischargeRate, ChargeRate, Voltage'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, creationflags=0x08000000 if os.name == 'nt' else 0, timeout=3)
        for line in res.stdout.splitlines():
            line = line.strip()
            if 'DischargeRate' in line or 'ChargeRate' in line:
                val = ''.join(c for c in line.split(':')[-1] if c.isdigit())
                if val:
                    rate_mw = int(val)
                    if rate_mw > 0:
                        power_watts = round(rate_mw / 1000.0, 1)
            elif 'Voltage' in line:
                val = ''.join(c for c in line.split(':')[-1] if c.isdigit())
                if val:
                    voltage_v = round(int(val) / 1000.0, 1)
    except Exception:
        pass

    return {
        'percent': pct,
        'has_battery': has_battery,
        'is_charging': is_charging,
        'ac_connected': ac,
        'time_remaining_sec': life_time,
        'battery_flag': status.BatteryFlag,
        'power_watts': power_watts,
        'voltage_v': voltage_v,
        'energy_saver': get_energy_saver_status(),
        'power_mode': get_active_power_scheme()
    }

def update_battery_report(force=False):
    global _cached_report_time
    now = time.time()
    # Refresh cache if older than 90 seconds or if forced
    if force or (now - _cached_report_time > 90) or not os.path.exists(_cached_report_path):
        try:
            subprocess.run(
                ['powercfg', '/batteryreport', '/xml', '/output', _cached_report_path],
                capture_output=True,
                creationflags=0x08000000 if os.name == 'nt' else 0, # CREATE_NO_WINDOW
                timeout=15
            )
            _cached_report_time = now
        except Exception as e:
            print(f"[battery_monitor] Warning running powercfg: {e}")

def detect_oem_battery_care(reported_design_cap=0, reported_full_cap=0):
    """
    Detects OEM Battery Health management features:
    - HP Adaptive Battery Optimizer / Extender
    - Lenovo Conservation Mode
    - ASUS Battery Health Charging
    - Dell Command Battery Care / Primary Batt Charge
    - Samsung Battery Protection / Battery Life Extender
    - Windows 11 Smart Charging
    """
    res = {
        'factory_design_capacity': None,
        'adaptive_battery_optimizer': 'Not Supported',
        'charge_limiter_active': False,
        'charge_limiter_name': None,
        'charge_limit_threshold': None,
        'oem_serial_number': None,
        'oem_design_voltage_mv': None,
        'oem_device_name': None,
        'oem_cycle_max': 1000
    }
    
    # 1. HP Support Assistant / HpHwDiag Configuration
    hp_configs = glob.glob(r'C:\Program Files\HP\HpHwDiag\Configuration\SystemConfiguration_*.json')
    if hp_configs:
        try:
            latest = max(hp_configs, key=os.path.getmtime)
            with open(latest, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                
                # Check Hardware -> Batteries
                hw_bats = data.get('Hardware', {}).get('Batteries', [])
                if hw_bats and isinstance(hw_bats, list):
                    b0 = hw_bats[0]
                    cap = b0.get('Capacity')
                    if cap and isinstance(cap, (int, float)) and cap > 1000:
                        res['factory_design_capacity'] = int(cap)
                    if b0.get('SerialNumber'):
                        res['oem_serial_number'] = str(b0.get('SerialNumber'))
                    if b0.get('Voltage'):
                        res['oem_design_voltage_mv'] = int(b0.get('Voltage'))
                    if b0.get('DeviceName'):
                        res['oem_device_name'] = str(b0.get('DeviceName'))
                
                ext_val = None
                ext_status = None
                def search_items(obj):
                    nonlocal ext_val, ext_status
                    if isinstance(obj, dict):
                        name = obj.get('Name')
                        val = obj.get('Value')
                        if name == 'Adaptive Battery Extender':
                            ext_val = val
                        elif name == 'Adaptive Battery Extender Status':
                            ext_status = val
                        for v in obj.values():
                            search_items(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            search_items(item)
                
                search_items(data)
                
                if ext_val or ext_status:
                    if ext_val == 'Enable' and ext_status == 'Activated':
                        res['adaptive_battery_optimizer'] = 'Enabled/Activated'
                        res['charge_limiter_active'] = True
                        res['charge_limiter_name'] = 'HP Adaptive Battery Optimizer'
                    elif ext_val == 'Enable':
                        res['adaptive_battery_optimizer'] = 'Enabled/Not Activated'
                        res['charge_limiter_active'] = True
                        res['charge_limiter_name'] = 'HP Adaptive Battery Optimizer'
                    elif ext_val == 'Disable':
                        res['adaptive_battery_optimizer'] = 'Disabled'
        except Exception:
            pass

    # 2. Lenovo Vantage / Conservation Mode Check
    try:
        key_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Lenovo\PWRMGRV\Data"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Lenovo\PowerManager\Data"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Lenovo\VantageService\AddinData\BatterySettings")
        ]
        for root_k, sub_k in key_paths:
            try:
                with winreg.OpenKey(root_k, sub_k) as k:
                    try:
                        val, _ = winreg.QueryValueEx(k, "U16RCON")
                        if val == 1:
                            res['charge_limiter_active'] = True
                            res['charge_limiter_name'] = 'Lenovo Conservation Mode (80%)'
                            res['charge_limit_threshold'] = 80
                            if res['adaptive_battery_optimizer'] == 'Not Supported':
                                res['adaptive_battery_optimizer'] = 'Enabled (Conservation Mode 80%)'
                    except:
                        pass
            except:
                pass
    except Exception:
        pass

    # 3. ASUS Battery Health Charging
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ASUS\ASUS System Control Interface\AsusOptimization\ASUS Battery Health Charging") as k:
            val, _ = winreg.QueryValueEx(k, "ChargingMode")
            if val in (1, 2):
                threshold = 80 if val == 1 else 60
                res['charge_limiter_active'] = True
                res['charge_limiter_name'] = f'ASUS Battery Health Charging ({threshold}%)'
                res['charge_limit_threshold'] = threshold
                if res['adaptive_battery_optimizer'] == 'Not Supported':
                    res['adaptive_battery_optimizer'] = f'Enabled ({threshold}% Limit)'
    except Exception:
        pass

    # 4. Samsung Battery Life Extender / Protect Battery
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Samsung\BatteryLifeExtender") as k:
            val, _ = winreg.QueryValueEx(k, "Enable")
            if val == 1:
                res['charge_limiter_active'] = True
                res['charge_limiter_name'] = 'Samsung Protect Battery (85%)'
                res['charge_limit_threshold'] = 85
                if res['adaptive_battery_optimizer'] == 'Not Supported':
                    res['adaptive_battery_optimizer'] = 'Enabled (85% Limit)'
    except Exception:
        pass

    # 5. Windows 11 Smart Charging
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\SmartCharging") as k:
            val, _ = winreg.QueryValueEx(k, "SmartChargingEnabled")
            if val == 1:
                res['charge_limiter_active'] = True
                res['charge_limiter_name'] = 'Windows Smart Charging'
                if res['adaptive_battery_optimizer'] == 'Not Supported':
                    res['adaptive_battery_optimizer'] = 'Enabled/Activated'
    except Exception:
        pass

    return res

def parse_report_data():
    update_battery_report()
    if not os.path.exists(_cached_report_path):
        return None

    try:
        tree = ET.parse(_cached_report_path)
        root = tree.getroot()
        ns = {'b': 'http://schemas.microsoft.com/battery/2012'}

        # 1. System & Batteries Info
        system_model = "Windows PC"
        mfg_node = root.find('.//b:SystemInformation/b:SystemProductName', ns)
        if mfg_node is not None and mfg_node.text:
            system_model = mfg_node.text.strip()
        else:
            mfg_name = root.find('.//b:SystemInformation/b:SystemManufacturer', ns)
            if mfg_name is not None and mfg_name.text:
                system_model = mfg_name.text.strip() + " Device"

        bat_nodes = root.findall('.//b:Batteries/b:Battery', ns)
        battery_info = {
            'device_model': system_model,
            'manufacturer': 'Unknown' if bat_nodes else 'Desktop Workstation',
            'chemistry': 'Li-ion' if bat_nodes else 'Continuous AC Line',
            'design_capacity': 0,
            'full_charge_capacity': 0,
            'cycle_count': None,
            'health_percent': 100.0,
            'has_battery': bool(bat_nodes)
        }
        for bat in bat_nodes:
            mfg = bat.find('b:Manufacturer', ns)
            if mfg is not None and mfg.text:
                battery_info['manufacturer'] = mfg.text.strip()
            chem = bat.find('b:Chemistry', ns)
            if chem is not None and chem.text:
                battery_info['chemistry'] = chem.text.strip()
            des = bat.find('b:DesignCapacity', ns)
            if des is not None and des.text:
                try: battery_info['design_capacity'] = int(des.text)
                except: pass
            ful = bat.find('b:FullChargeCapacity', ns)
            if ful is not None and ful.text:
                try: battery_info['full_charge_capacity'] = int(ful.text)
                except: pass
            cyc = bat.find('b:CycleCount', ns)
            if cyc is not None and cyc.text:
                try: battery_info['cycle_count'] = int(cyc.text)
                except: pass

        # OEM Battery Care & Adaptive Optimizer check
        oem_care = detect_oem_battery_care(battery_info['design_capacity'], battery_info['full_charge_capacity'])
        battery_info['adaptive_battery_optimizer'] = oem_care.get('adaptive_battery_optimizer', 'Not Supported')
        battery_info['charge_limiter_active'] = oem_care.get('charge_limiter_active', False)
        battery_info['charge_limiter_name'] = oem_care.get('charge_limiter_name')
        battery_info['charge_limit_threshold'] = oem_care.get('charge_limit_threshold')
        battery_info['cycle_count_max'] = oem_care.get('oem_cycle_max', 1000)
        
        if oem_care.get('factory_design_capacity'):
            battery_info['factory_design_capacity'] = oem_care['factory_design_capacity']
            # Compare with true factory design capacity (e.g. 70,070 mWh / 70 WHr)
            battery_info['design_capacity'] = oem_care['factory_design_capacity']
        else:
            battery_info['factory_design_capacity'] = battery_info['design_capacity']

        if oem_care.get('oem_serial_number'):
            battery_info['serial_number'] = oem_care['oem_serial_number']
        if oem_care.get('oem_design_voltage_mv'):
            battery_info['design_voltage_mv'] = oem_care['oem_design_voltage_mv']
        if oem_care.get('oem_device_name'):
            battery_info['device_name'] = oem_care['oem_device_name']

        # Calculate true health percentage against factory design capacity
        if battery_info['design_capacity'] > 0:
            health = round((battery_info['full_charge_capacity'] / battery_info['design_capacity']) * 100, 1)
            battery_info['health_percent'] = min(100.0, health)

        # WHr equivalents
        battery_info['design_wh'] = round(battery_info['design_capacity'] / 1000.0)
        battery_info['full_charge_wh'] = round(battery_info['full_charge_capacity'] / 1000.0)

        # 2. Parse Recent Usage
        recent_entries = []
        for e in root.findall('.//b:RecentUsage/b:UsageEntry', ns):
            attr = e.attrib
            try:
                ts = attr.get('LocalTimestamp') or attr.get('Timestamp')
                if not ts:
                    continue
                dt = datetime.datetime.fromisoformat(ts.replace('Z', ''))
                entry_type = attr.get('EntryType', '')
                dur_str = attr.get('Duration', '0')
                # Duration in 100-nanosecond units (filetime ticks)
                dur_sec = int(dur_str) / 10000000.0 if dur_str else 0
                if dur_sec < 0 or dur_sec > 86400 * 7 or entry_type == 'ReportGenerated':
                    dur_sec = 0
                charge_cap = int(attr.get('ChargeCapacity', 0))
                full_cap = int(attr.get('FullChargeCapacity', battery_info['full_charge_capacity']))
                ac = int(attr.get('Ac', 0))
                pct = round((charge_cap / max(1, full_cap)) * 100.0, 1) if full_cap > 0 else 0

                recent_entries.append({
                    'timestamp': dt.isoformat(),
                    'datetime': dt,
                    'entry_type': entry_type,
                    'ac': ac,
                    'charge_mwh': charge_cap,
                    'full_mwh': full_cap,
                    'percent': min(100.0, max(0.0, pct)),
                    'duration_sec': dur_sec
                })
            except Exception as ex:
                continue

        # Sort entries by datetime
        recent_entries.sort(key=lambda x: x['datetime'])

        # 3. Parse EnergyDrains for granular graph curve
        drain_points = []
        for d in root.findall('.//b:EnergyDrains/b:Drain', ns):
            attr = d.attrib
            try:
                start_ts = attr.get('LocalStartTimestamp') or attr.get('StartTimestamp')
                end_ts = attr.get('LocalEndTimestamp') or attr.get('EndTimestamp')
                if not start_ts or not end_ts:
                    continue
                s_dt = datetime.datetime.fromisoformat(start_ts.replace('Z', ''))
                e_dt = datetime.datetime.fromisoformat(end_ts.replace('Z', ''))
                s_cap = int(attr.get('StartChargeCapacity', 0))
                s_full = int(attr.get('StartFullChargeCapacity', battery_info['full_charge_capacity']))
                e_cap = int(attr.get('EndChargeCapacity', 0))
                e_full = int(attr.get('EndFullChargeCapacity', battery_info['full_charge_capacity']))

                s_pct = round((s_cap / max(1, s_full)) * 100.0, 1)
                e_pct = round((e_cap / max(1, e_full)) * 100.0, 1)

                drain_points.append({
                    'start_dt': s_dt,
                    'end_dt': e_dt,
                    'start_pct': s_pct,
                    'end_pct': e_pct,
                    'start_cap': s_cap,
                    'end_cap': e_cap
                })
            except Exception:
                continue

        drain_points.sort(key=lambda x: x['start_dt'])

        # 4. Parse 7-day History
        history_days = []
        for h in root.findall('.//b:History/b:HistoryEntry', ns):
            attr = h.attrib
            try:
                end_ts = attr.get('LocalEndDate') or attr.get('EndDate')
                if not end_ts:
                    continue
                e_dt = datetime.datetime.fromisoformat(end_ts.replace('Z', ''))
                # ActiveDcEnergy, CsDcEnergy
                active_dc = int(attr.get('ActiveDcEnergy', 0))
                cs_dc = int(attr.get('CsDcEnergy', 0))
                total_dc_mwh = active_dc + cs_dc
                full_cap = int(attr.get('FullChargeCapacity', battery_info['full_charge_capacity']))
                pct_drain = round((total_dc_mwh / max(1, full_cap)) * 100, 1) if full_cap > 0 else 0

                # Duration strings are ISO-8601 like PT3H38M33S
                def parse_iso_dur(d_str):
                    if not d_str or not d_str.startswith('P'):
                        return 0
                    sec = 0
                    cur = ''
                    in_time = False
                    for char in d_str:
                        if char == 'T':
                            in_time = True
                            continue
                        if char.isdigit():
                            cur += char
                        elif char == 'D':
                            sec += int(cur or 0) * 86400
                            cur = ''
                        elif char == 'H':
                            sec += int(cur or 0) * 3600
                            cur = ''
                        elif char == 'M':
                            sec += int(cur or 0) * 60
                            cur = ''
                        elif char == 'S':
                            sec += int(cur or 0)
                            cur = ''
                    return sec

                active_sec = parse_iso_dur(attr.get('ActiveDcTime', ''))
                cs_sec = parse_iso_dur(attr.get('CsDcTime', ''))

                history_days.append({
                    'date': e_dt.strftime('%a, %b %d'),
                    'datetime_iso': e_dt.isoformat(),
                    'screen_on_sec': active_sec,
                    'screen_off_sec': cs_sec,
                    'percent_drained': pct_drain,
                    'mwh_drained': total_dc_mwh
                })
            except Exception:
                continue

        history_days.sort(key=lambda x: x['datetime_iso'])

        return {
            'battery_info': battery_info,
            'recent_entries': recent_entries,
            'drain_points': drain_points,
            'history_days': history_days
        }

    except Exception as e:
        print(f"[battery_monitor] Error parsing XML: {e}")
        return None

def build_view_stats(mode='since_charge'):
    """
    mode: 'since_charge', 'today', 'week'
    Returns:
      - graph_points: [{ time: '14:00', percent: 52, is_charging: false, timestamp: ISO }]
      - charging_blocks: [{ start_time, end_time, start_pct, end_pct }]
      - screen_on_time: '2h 15m'
      - screen_off_time: '1h 40m'
      - screen_on_sec: int
      - screen_off_sec: int
      - total_drain_pct: float
      - since_label: 'Since 12:04 PM (100%)'
      - current_percent: float
      - is_charging: bool
    """
    data = parse_report_data()
    live = get_live_power_status()
    now_dt = datetime.datetime.now()

    if not data or not data['recent_entries']:
        # Fallback to simulated/live single point if no entries
        return {
            'graph_points': [{
                'time': now_dt.strftime('%H:%M'),
                'percent': live['percent'],
                'is_charging': live['is_charging'],
                'timestamp': now_dt.isoformat()
            }],
            'charging_blocks': [],
            'screen_on_sec': 0,
            'screen_off_sec': 0,
            'screen_on_fmt': '0m',
            'screen_off_fmt': '0m',
            'total_drain_pct': 0,
            'since_label': 'Live'
        }

    entries = data['recent_entries']
    drain_pts = data['drain_points']

    # Determine window start
    if mode == 'since_charge':
        # Find start of last discharge cycle that began at >= 90%
        full_idx = -1
        if not live['ac_connected'] or live['percent'] < 95:
            # Currently running on battery: find when it was last unplugged / at full charge
            for i in range(len(entries) - 1, -1, -1):
                e = entries[i]
                if e.get('entry_type') != 'ReportGenerated' and e.get('percent', 0) >= 90:
                    full_idx = i
                    break
        else:
            # Currently plugged in or at 100%: find the start of the full discharge cycle
            for i in range(len(entries) - 1, -1, -1):
                e = entries[i]
                if e.get('entry_type') != 'ReportGenerated' and e.get('percent', 0) >= 90:
                    # Check if there was substantial battery discharge after this entry
                    has_discharge = any(entries[j].get('percent', 100) <= 90 for j in range(i, len(entries)))
                    if has_discharge:
                        full_idx = i
                        while full_idx > 0 and entries[full_idx - 1].get('percent', 0) >= 90 and entries[full_idx - 1].get('ac') == 0:
                            full_idx -= 1
                        break
        
        if full_idx >= 0:
            start_entry = entries[full_idx]
            start_dt = start_entry['datetime']
            since_label = f"Since {start_dt.strftime('%I:%M %p')} • today"
            relevant_entries = entries[full_idx:]
        else:
            # Fallback if never reached 90% in recent entries
            start_entry = entries[max(0, len(entries) - 8)]
            start_dt = start_entry['datetime']
            since_label = f"Since {start_dt.strftime('%I:%M %p')}"
            relevant_entries = entries[max(0, len(entries) - 8):]

    elif mode == 'today':
        start_dt = now_dt - datetime.timedelta(hours=24)
        since_label = "Last 24 hours"
        relevant_entries = [e for e in entries if e['datetime'] >= start_dt and e.get('entry_type') != 'ReportGenerated']
        if not relevant_entries and entries:
            relevant_entries = [entries[-1]]

    else: # 'week'
        start_dt = now_dt - datetime.timedelta(days=7)
        since_label = "Last 7 days"
        relevant_entries = [e for e in entries if e['datetime'] >= start_dt and e.get('entry_type') != 'ReportGenerated']

    # Calculate Screen On (Active) and Screen Off (Suspend/ConnectedStandby)
    screen_on_sec = 0
    screen_off_sec = 0

    if mode == 'week' and data.get('history_days'):
        for h in data['history_days'][-7:]:
            screen_on_sec += h.get('screen_on_sec', 0)
            screen_off_sec += h.get('screen_off_sec', 0)
        # Add today's active session
        for e in relevant_entries:
            if e['datetime'].date() == now_dt.date():
                if e['entry_type'] == 'Active':
                    screen_on_sec += e['duration_sec']
                elif e['entry_type'] in ('ConnectedStandby', 'Suspend'):
                    screen_off_sec += e['duration_sec']
    else:
        for e in relevant_entries:
            dur = e['duration_sec']
            if e['entry_type'] == 'Active':
                screen_on_sec += dur
            elif e['entry_type'] in ('ConnectedStandby', 'Suspend'):
                screen_off_sec += dur

        # Add duration from last entry up to now
        if relevant_entries:
            last_e = relevant_entries[-1]
            delta_since_last = max(0, min(86400, (now_dt - last_e['datetime']).total_seconds()))
            screen_on_sec += delta_since_last

    # Format Screen On / Screen Off
    def fmt_dur(sec):
        sec = max(0, int(sec))
        h = sec // 3600
        m = (sec % 3600) // 60
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    # Build Graph Points
    graph_points = []
    charging_blocks = []

    if mode == 'week':
        # In week mode, plot daily data points
        hist = data.get('history_days', [])[-7:]
        if hist:
            for h in hist:
                d_pct = max(10, min(100, 100.0 - h.get('percent_drained', 0)))
                lbl = h.get('date', '').split(',')[0] # 'Fri', 'Sat' etc.
                graph_points.append({
                    'time': lbl,
                    'time_label': lbl,
                    'timestamp': h.get('datetime_iso', ''),
                    'percent': d_pct,
                    'is_charging': False
                })
        # Add today point
        graph_points.append({
            'time': 'Today',
            'time_label': 'Today',
            'timestamp': now_dt.isoformat(),
            'percent': live['percent'],
            'is_charging': live['is_charging']
        })
    else:
        # Filter drain points in range
        window_drains = [d for d in drain_pts if d['end_dt'] >= start_dt and d['start_dt'] <= now_dt]

        for d in window_drains:
            t_start = d['start_dt'].strftime('%I:%M %p')
            graph_points.append({
                'time': t_start,
                'time_label': t_start,
                'timestamp': d['start_dt'].isoformat(),
                'percent': d['start_pct'],
                'is_charging': d['end_pct'] > d['start_pct']
            })
            t_end = d['end_dt'].strftime('%I:%M %p')
            graph_points.append({
                'time': t_end,
                'time_label': t_end,
                'timestamp': d['end_dt'].isoformat(),
                'percent': d['end_pct'],
                'is_charging': d['end_pct'] > d['start_pct']
            })

        # Merge relevant_entries points for exact inflection points (AC plug-in, charge start)
        for e in relevant_entries:
            if e.get('entry_type') != 'ReportGenerated':
                t_fmt = e['datetime'].strftime('%I:%M %p')
                graph_points.append({
                    'time': t_fmt,
                    'time_label': t_fmt,
                    'timestamp': e['timestamp'],
                    'percent': e['percent'],
                    'is_charging': e['ac'] == 1
                })

        # Always append current live point
        now_lbl = f"Now - {now_dt.strftime('%I:%M %p')}"
        graph_points.append({
            'time': now_lbl,
            'time_label': now_lbl,
            'timestamp': now_dt.isoformat(),
            'percent': live['percent'],
            'is_charging': live['is_charging']
        })

    # Sort & deduplicate close points
    graph_points.sort(key=lambda p: p['timestamp'])
    cleaned_points = []
    seen_times = set()
    for p in graph_points:
        key = p['time_label']
        if key not in seen_times:
            seen_times.add(key)
            cleaned_points.append(p)

    # Detect Charging blocks (intervals where laptop was on AC) safely
    for e in relevant_entries:
        if e['ac'] == 1 and e.get('entry_type') != 'ReportGenerated':
            dur = max(0, min(86400 * 2, e.get('duration_sec', 0)))
            try:
                end_dt = e['datetime'] + datetime.timedelta(seconds=dur)
                if end_dt > now_dt:
                    end_dt = now_dt
                end_time = end_dt.isoformat()
            except Exception:
                end_time = e['datetime'].isoformat()
            charging_blocks.append({
                'start_time': e['timestamp'],
                'end_time': end_time,
                'start_pct': e['percent']
            })

    # Total drain calculation
    if mode == 'week' and data.get('history_days'):
        total_drain = round(sum(h.get('percent_drained', 0) for h in data['history_days'][-7:]), 1)
    else:
        # Calculate sum of discharge drops in the window so recharging doesn't erase discharge history
        drain_sum = 0.0
        for i in range(1, len(cleaned_points)):
            prev_p = cleaned_points[i-1]['percent']
            curr_p = cleaned_points[i]['percent']
            if prev_p > curr_p:
                drain_sum += (prev_p - curr_p)
        total_drain = round(drain_sum, 1)
        if total_drain == 0.0 and cleaned_points:
            first_pct = cleaned_points[0]['percent']
            curr_pct = live['percent']
            total_drain = max(0.0, round(first_pct - curr_pct, 1))

    return {
        'mode': mode,
        'since_label': since_label,
        'screen_on_sec': int(screen_on_sec),
        'screen_off_sec': int(screen_off_sec),
        'screen_on_fmt': fmt_dur(screen_on_sec),
        'screen_off_fmt': fmt_dur(screen_off_sec),
        'screen_on_formatted': fmt_dur(screen_on_sec),
        'screen_off_formatted': fmt_dur(screen_off_sec),
        'total_drain_pct': total_drain,
        'graph_points': cleaned_points,
        'charging_blocks': charging_blocks,
        'history_days': data['history_days'][-7:],
        'battery_specs': data['battery_info'],
        'live': live
    }

if __name__ == '__main__':
    st = build_view_stats('since_charge')
    print("Mode:", st['mode'])
    print("Label:", st['since_label'])
    print("Screen on:", st['screen_on_fmt'])
    print("Screen off:", st['screen_off_fmt'])
    print("Total drain:", st['total_drain_pct'], "%")
    print("Graph points count:", len(st['graph_points']))
    print("Live percent:", st['live']['percent'], "Charging:", st['live']['is_charging'])
