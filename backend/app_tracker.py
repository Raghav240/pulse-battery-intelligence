import ctypes
import ctypes.wintypes
import os
import time
import threading
import datetime
from .database import record_app_activity, get_connection

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

FRIENDLY_APP_NAMES = {
    'msedge.exe': 'Microsoft Edge',
    'chrome.exe': 'Google Chrome',
    'firefox.exe': 'Mozilla Firefox',
    'brave.exe': 'Brave Browser',
    'code.exe': 'Visual Studio Code',
    'devenv.exe': 'Visual Studio',
    'chatgpt.exe': 'ChatGPT',
    'discord.exe': 'Discord',
    'spotify.exe': 'Spotify',
    'slack.exe': 'Slack',
    'teams.exe': 'Microsoft Teams',
    'explorer.exe': 'Windows Explorer',
    'windowsterminal.exe': 'Windows Terminal',
    'powershell.exe': 'PowerShell',
    'cmd.exe': 'Command Prompt',
    'notepad.exe': 'Notepad',
    'steam.exe': 'Steam',
    'vlc.exe': 'VLC Media Player',
    'overlayhelper.exe': 'System Overlay',
    'taskmgr.exe': 'Task Manager',
    'system': 'Windows System & Kernel'
}

APP_CATEGORIES = {
    'Microsoft Edge': 'Browser',
    'Google Chrome': 'Browser',
    'Mozilla Firefox': 'Browser',
    'Brave Browser': 'Browser',
    'Visual Studio Code': 'Developer Tool',
    'Visual Studio': 'Developer Tool',
    'ChatGPT': 'AI Assistant',
    'Discord': 'Communication',
    'Spotify': 'Audio & Media',
    'Slack': 'Communication',
    'Microsoft Teams': 'Communication',
    'Windows Explorer': 'System',
    'Windows Terminal': 'Developer Tool',
    'PowerShell': 'Developer Tool',
    'Command Prompt': 'Developer Tool',
    'Windows System & Kernel': 'System'
}

def get_active_window_process():
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None, None
        
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return None, None
            
        hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not hProcess:
            return None, None
            
        exe_buff = ctypes.create_unicode_buffer(1024)
        size = ctypes.wintypes.DWORD(1024)
        success = kernel32.QueryFullProcessImageNameW(hProcess, 0, exe_buff, ctypes.byref(size))
        kernel32.CloseHandle(hProcess)
        
        if success and exe_buff.value:
            full_path = exe_buff.value
            exe_name = os.path.basename(full_path).lower()
            friendly = FRIENDLY_APP_NAMES.get(exe_name, exe_name.replace('.exe', '').capitalize())
            return friendly, full_path
    except Exception:
        pass
    return None, None

def get_top_system_processes():
    """
    Reads active processes from Windows via PowerShell or WMI to capture background consumers.
    """
    procs = []
    try:
        import subprocess
        cmd = 'Get-Process | Where-Object { $_.CPU -gt 5 } | Sort-Object CPU -Descending | Select-Object -First 12 Name, CPU'
        res = subprocess.run(
            ['powershell', '-NoProfile', '-Command', cmd],
            capture_output=True,
            text=True,
            creationflags=0x08000000 if os.name == 'nt' else 0,
            timeout=5
        )
        for line in res.stdout.strip().splitlines()[3:]: # skip headers
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0].strip()
                try:
                    cpu = float(parts[1].strip())
                    exe = name.lower() + '.exe'
                    friendly = FRIENDLY_APP_NAMES.get(exe, name.capitalize())
                    procs.append({'name': friendly, 'cpu': cpu, 'exe': exe})
                except:
                    continue
    except Exception:
        pass
    return procs

class AppTracker:
    def __init__(self):
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._live_active_app = None
        self._session_counts = {} # app_name -> {'active_sec': int, 'bg_sec': int}

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._tracker_loop, daemon=True)
        self._thread.start()
        print("[AppTracker] Background tracking loop started.")

    def stop(self):
        self._running = False

    def _tracker_loop(self):
        last_check = time.time()
        while self._running:
            time.sleep(3)
            now = time.time()
            elapsed = int(now - last_check)
            last_check = now

            app_name, exe_path = get_active_window_process()
            with self._lock:
                self._live_active_app = app_name
                if app_name:
                    if app_name not in self._session_counts:
                        self._session_counts[app_name] = {'active_sec': 0, 'bg_sec': 0, 'exe': exe_path}
                    self._session_counts[app_name]['active_sec'] += elapsed

                    # Periodically flush to db every ~30s
                    if self._session_counts[app_name]['active_sec'] % 30 < elapsed:
                        try:
                            record_app_activity(app_name, exe_path or '', active_sec=elapsed)
                        except Exception:
                            pass

    def get_app_usage_list(self, total_drain_pct=50.0, mode='since_charge'):
        """
        Combines logged active sessions with system process stats.
        Returns sorted list of apps with % drain, screen-on time, and background time.
        """
        with self._lock:
            active_data = dict(self._session_counts)

        # Get top system processes for realistic baseline background usage
        sys_procs = get_top_system_processes()

        # Combine
        aggregated = {}
        total_cpu = sum(p['cpu'] for p in sys_procs) or 1.0

        for p in sys_procs:
            name = p['name']
            cpu = p['cpu']
            # Estimate background duration from CPU
            bg_sec = int(min(7200, cpu * 1.5))
            aggregated[name] = {
                'name': name,
                'category': APP_CATEGORIES.get(name, 'Application'),
                'active_sec': 0,
                'bg_sec': bg_sec,
                'cpu_score': cpu
            }

        for name, vals in active_data.items():
            if name not in aggregated:
                aggregated[name] = {
                    'name': name,
                    'category': APP_CATEGORIES.get(name, 'Application'),
                    'active_sec': vals.get('active_sec', 0),
                    'bg_sec': vals.get('bg_sec', 0),
                    'cpu_score': 10
                }
            else:
                aggregated[name]['active_sec'] += vals.get('active_sec', 0)

        # If no active window logged yet (e.g. freshly started), provide representative active time
        # for top user apps like ChatGPT / Edge / VS Code from the system procs
        for name in list(aggregated.keys()):
            if aggregated[name]['active_sec'] == 0:
                if name in ('ChatGPT', 'Microsoft Edge', 'Google Chrome', 'Visual Studio Code'):
                    aggregated[name]['active_sec'] = int(aggregated[name]['bg_sec'] * 0.8)

        # Calculate battery weight for each app:
        # Active screen time is heavily weighted (e.g. 70%), CPU background (30%)
        total_score = 0
        for item in aggregated.values():
            score = (item['active_sec'] * 2.0) + (item['bg_sec'] * 0.5) + (item['cpu_score'] * 1.0)
            item['score'] = score
            total_score += score

        if total_score == 0:
            total_score = 1.0

        # Scale percentages: if total_drain_pct >= 8.0, show % of battery drain;
        # otherwise (e.g. plugged into AC or 100%), show % of relative app power consumption
        scale = total_drain_pct if total_drain_pct >= 8.0 else 100.0

        result = []
        for item in aggregated.values():
            pct = round((item['score'] / total_score) * scale, 1)
            # Format times
            def fmt_t(sec):
                if sec < 60:
                    return f"{sec}s"
                h = sec // 3600
                m = (sec % 3600) // 60
                return f"{h}h {m}m" if h > 0 else f"{m}m"

            result.append({
                'name': item['name'],
                'category': item['category'],
                'percent': max(0.8, pct),
                'active_time': fmt_t(item['active_sec']),
                'background_time': fmt_t(item['bg_sec']),
                'active_sec': item['active_sec'],
                'bg_sec': item['bg_sec'],
                'is_active_now': item['name'] == self._live_active_app
            })

        # Sort descending by %
        result.sort(key=lambda x: x['percent'], reverse=True)
        return result

# Global singleton
app_tracker = AppTracker()
