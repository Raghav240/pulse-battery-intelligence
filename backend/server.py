import os
import sys
from pathlib import Path
import secrets

# Ensure stdout and stderr exist in windowless GUI mode
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import http.server
import socketserver
import json
import urllib.parse
import mimetypes
import winsound
import threading
import time
import datetime
from .battery_monitor import build_view_stats, get_live_power_status, update_battery_report, parse_report_data
from .app_tracker import app_tracker
from .database import init_db, record_battery_sample, record_charge_cycle
from .hardware_monitor import get_complete_hardware_telemetry, set_hardware_fan_profile

PORT = 5055
API_TOKEN = secrets.token_urlsafe(32)
ALLOWED_ORIGINS = {'http://127.0.0.1:5055', 'http://localhost:5055', 'http://localhost:5173', 'http://127.0.0.1:5173'}
_last_sample_ac = None
_open_cycle = None

if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    STATIC_DIR = os.path.join(BASE_DIR, 'app', 'dist')
    SETTINGS_FILE = os.path.join(os.path.dirname(sys.executable), 'settings.json')
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, 'app', 'dist')
    SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

def load_settings():
    default_settings = {
        'protect_alert': True,
        'protect_limit': 80,
        'low_alert': 20,
        'refresh_sec': 15,
        'performance_mode': 'Balanced',
        'fan_profile': 'Balanced',
        'overlay_hotkey': 'Ctrl+Shift+B',
        'start_with_windows': False
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return {**default_settings, **json.load(f)}
        except:
            pass
    return default_settings

def save_settings(s):
    allowed_modes = {'Silent', 'Quiet', 'Balanced', 'Performance', 'Turbo'}
    merged = {**load_settings(), **(s if isinstance(s, dict) else {})}
    merged['protect_alert'] = bool(merged.get('protect_alert', True))
    try:
        merged['protect_limit'] = min(100, max(60, int(merged.get('protect_limit', 80))))
    except (TypeError, ValueError):
        merged['protect_limit'] = 80
    try:
        merged['low_alert'] = min(50, max(5, int(merged.get('low_alert', 20))))
    except (TypeError, ValueError):
        merged['low_alert'] = 20
    try:
        merged['refresh_sec'] = min(300, max(5, int(merged.get('refresh_sec', 15))))
    except (TypeError, ValueError):
        merged['refresh_sec'] = 15
    merged['performance_mode'] = merged.get('performance_mode', 'Balanced')
    merged['fan_profile'] = merged.get('fan_profile', 'Balanced')
    if merged['performance_mode'] not in allowed_modes:
        merged['performance_mode'] = 'Balanced'
    if merged['fan_profile'] not in allowed_modes:
        merged['fan_profile'] = 'Balanced'
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(merged, f, indent=2)
        return merged
    except:
        return load_settings()

_last_client_seen = time.time()

def record_client_activity():
    global _last_client_seen
    _last_client_seen = time.time()

def get_last_client_seen():
    return _last_client_seen

def sample_telemetry_loop():
    global _last_sample_ac, _open_cycle
    while True:
        try:
            settings = load_settings()
            interval = min(300, max(5, int(settings.get('refresh_sec', 15))))
            live = get_live_power_status()
            hardware = get_complete_hardware_telemetry(profile=settings.get('fan_profile', 'Balanced'))
            cpu_temp = hardware.get('thermals', {}).get('cpu_temp_c')
            gpu_temp = hardware.get('thermals', {}).get('gpu_temp_c')
            fans = hardware.get('fans', {})
            record_battery_sample(
                percent=live.get('percent', 0),
                is_charging=live.get('is_charging', False),
                time_remaining_sec=live.get('time_remaining_sec'),
                power_watts=live.get('power_watts'),
                voltage_v=live.get('voltage_v'),
                cpu_temp_c=cpu_temp,
                gpu_temp_c=gpu_temp,
                cpu_fan_rpm=fans.get('cpu_fan_rpm') if fans.get('available') else None,
                gpu_fan_rpm=fans.get('gpu_fan_rpm') if fans.get('available') else None
            )
            ac = live.get('ac_connected')
            if _last_sample_ac is True and ac is False:
                _open_cycle = {'unplugged_at': time.time(), 'start_percent': live.get('percent', 0)}
            elif _last_sample_ac is False and ac is True and _open_cycle:
                record_charge_cycle(
                    unplugged_at=datetime.datetime.fromtimestamp(_open_cycle['unplugged_at']).isoformat(),
                    start_percent=_open_cycle['start_percent'],
                    end_percent=live.get('percent', 0),
                    plugged_at=datetime.datetime.now().isoformat()
                )
                _open_cycle = None
            _last_sample_ac = ac
            time.sleep(interval)
        except Exception as exc:
            print(f'[sampler] {exc}')
            time.sleep(15)
_last_alert_time = 0

def alert_monitor_loop():
    global _last_alert_time
    while True:
        time.sleep(5)
        try:
            live = get_live_power_status()
            settings = load_settings()
            limit = settings.get('protect_limit', 80)
            now = time.time()

            # If charging and reached or exceeded threshold (and limit != 100)
            low_alert = settings.get('low_alert', 20)
            if ((settings.get('protect_alert', True) and limit < 100 and live['is_charging'] and live['percent'] >= limit) or
                (live.get('has_battery', True) and not live.get('ac_connected') and
                 live.get('percent', 100) <= low_alert)):
                # Fired once every 5 minutes to avoid spam
                if now - _last_alert_time > 300:
                    _last_alert_time = now
                    try:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                        print(f"[Alert] Battery reached {live['percent']}%! Please disconnect charger.")
                    except:
                        pass
        except Exception:
            pass

class BatteryApiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR if os.path.exists(STATIC_DIR) else None, **kwargs)

    def _send_json(self, data, status_code=200):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        origin = self.headers.get('Origin')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        origin = self.headers.get('Origin')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        record_client_activity()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/api/heartbeat':
            self._send_json({'status': 'ok', 'time': time.time()})
            return

        if path == '/api/session':
            self._send_json({'token': API_TOKEN})
            return

        if path == '/api/settings':
            self._send_json(load_settings())
            return

        if path == '/api/hardware/telemetry':
            s = load_settings()
            tel = get_complete_hardware_telemetry(profile=s.get('fan_profile', 'Balanced'))
            self._send_json(tel)
            return

        if path == '/api/battery/status':
            live = get_live_power_status()
            report = parse_report_data()
            specs = report['battery_info'] if report else {}
            specs['has_battery'] = live.get('has_battery', True)
            s = load_settings()
            hardware = get_complete_hardware_telemetry(profile=s.get('fan_profile', 'Balanced'))
            
            # Format remaining time
            sec = live.get('time_remaining_sec', -1)
            time_fmt = None
            if sec > 0:
                h = sec // 3600
                m = (sec % 3600) // 60
                time_fmt = f"{h}h {m}m remaining" if h > 0 else f"{m}m remaining"
            elif live.get('is_charging'):
                time_fmt = f"Charging at {hardware['power_flow']['battery_watts']} W"
            elif live.get('ac_connected'):
                time_fmt = f"Plugged in ({hardware['power_flow']['charger_push_watts']} W push)"
            else:
                time_fmt = "Estimating remaining time..."

            self._send_json({
                'live': live,
                'time_remaining_formatted': time_fmt,
                'specs': specs,
                'hardware': hardware,
                'settings': s
            })
            return

        if path == '/api/battery/stats':
            mode = query.get('mode', ['since_charge'])[0]
            stats = build_view_stats(mode)
            self._send_json(stats)
            return

        if path == '/api/apps/usage':
            mode = query.get('mode', ['since_charge'])[0]
            # Get current total drain to scale percentages accurately
            stats = build_view_stats(mode)
            total_drain = stats.get('total_drain_pct', 50.0)
            apps = app_tracker.get_app_usage_list(total_drain_pct=total_drain, mode=mode)
            self._send_json({
                'mode': mode,
                'total_drain_pct': total_drain,
                'apps': apps
            })
            return

        if path == '/api/battery/specs':
            report = parse_report_data()
            self._send_json(report['battery_info'] if report else {})
            return

        # Serve static assets from dist
        if os.path.exists(STATIC_DIR):
            static_root = Path(STATIC_DIR).resolve()
            req_file = (static_root / urllib.parse.unquote(path.lstrip('/'))).resolve()
            if static_root not in req_file.parents and req_file != static_root:
                self._send_json({'error': 'Not found'}, status_code=404)
                return
            if not os.path.exists(req_file) or os.path.isdir(req_file):
                # Fallback to index.html for SPA client-side routing
                req_file = os.path.join(STATIC_DIR, 'index.html')
            
            if os.path.exists(req_file):
                mime, _ = mimetypes.guess_type(req_file)
                try:
                    with open(req_file, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', mime or 'text/html')
                    self.send_header('Content-Length', str(len(content)))
                    origin = self.headers.get('Origin')
                    if origin in ALLOWED_ORIGINS:
                        self.send_header('Access-Control-Allow-Origin', origin)
                        self.send_header('Vary', 'Origin')
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                    return
                except Exception as e:
                    try:
                        self.send_error(500, str(e))
                    except:
                        pass
                    return

        # Default fallback if dist is not yet built
        self._send_json({'status': 'Battery API service running', 'ui_ready': os.path.exists(STATIC_DIR)})

    def do_POST(self):
        if self.headers.get('X-Pulse-Token') != API_TOKEN:
            self._send_json({'error': 'Unauthorized'}, status_code=401)
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/settings':
            content_length = int(self.headers.get('Content-Length', 0) or 0)
            if content_length <= 0 or content_length > 65536:
                self._send_json({'error': 'Invalid request body'}, status_code=400)
                return
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                save_settings(data)
                self._send_json({'success': True, 'settings': load_settings()})
            except Exception as e:
                self._send_json({'error': str(e)}, status_code=400)
            return

        if path == '/api/action/open_windows_settings':
            try:
                os.startfile('ms-settings:batterysaver')
                self._send_json({'success': True})
            except Exception:
                try:
                    os.startfile('ms-settings:powersleep')
                    self._send_json({'success': True})
                except Exception as e:
                    self._send_json({'error': str(e)}, status_code=500)
            return

        if path == '/api/action/set_fan_profile':
            content_length = int(self.headers.get('Content-Length', 0) or 0)
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                prof = data.get('profile', 'Balanced')
                if prof not in {'Silent', 'Quiet', 'Balanced', 'Performance', 'Turbo'}:
                    raise ValueError('Invalid fan profile')
                set_hardware_fan_profile(prof)
                s = load_settings()
                s['fan_profile'] = prof
                save_settings(s)
                self._send_json({'success': True, 'profile': prof})
            except Exception as e:
                self._send_json({'error': str(e)}, status_code=500)
            return

        if path == '/api/action/set_power_mode':
            content_length = int(self.headers.get('Content-Length', 0) or 0)
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                mode = data.get('mode', 'Balanced')
                if mode not in {'Silent', 'Quiet', 'Balanced', 'Performance', 'Turbo'}:
                    raise ValueError('Invalid power mode')
                mode_key = mode.lower()
                # Windows Power Schemes GUIDs
                schemes = {
                    'silent': 'a1841308-3541-4fab-bc81-f71556f20b4a', # Power Saver
                    'quiet': 'a1841308-3541-4fab-bc81-f71556f20b4a',
                    'balanced': '381b4222-f694-41f0-9685-ff5bb260df2e', # Balanced
                    'performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c' # High Performance
                }
                guid = schemes.get(mode_key, schemes['balanced'])
                import subprocess
                subprocess.run(['powercfg', '/setactive', guid], creationflags=0x08000000 if os.name == 'nt' else 0)
                # Also set fan policy in sync
                set_hardware_fan_profile(mode)
                s = load_settings()
                s['performance_mode'] = mode
                s['fan_profile'] = mode
                save_settings(s)
                self._send_json({'success': True, 'mode': mode, 'settings': s})
            except Exception as e:
                self._send_json({'error': str(e)}, status_code=500)
            return

        if path == '/api/action/refresh':
            update_battery_report(force=True)
            self._send_json({'success': True, 'message': 'Battery report refreshed'})
            return

        self._send_json({'error': 'Not found'}, status_code=404)

def run_server(port=PORT):
    init_db()
    
    # Start background components without blocking port binding
    threading.Thread(target=app_tracker.start, daemon=True).start()
    threading.Thread(target=update_battery_report, daemon=True).start()
    threading.Thread(target=alert_monitor_loop, daemon=True).start()
    threading.Thread(target=sample_telemetry_loop, daemon=True).start()
    
    # Use multi-threaded TCP server to handle concurrent polling and static assets cleanly
    class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True

    with ThreadedServer(('127.0.0.1', port), BatteryApiHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            app_tracker.stop()

if __name__ == '__main__':
    run_server()
