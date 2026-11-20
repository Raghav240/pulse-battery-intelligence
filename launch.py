import os
import sys

# Ensure stdout and stderr exist in windowless GUI mode
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import time
import subprocess
import threading
import urllib.request
import webbrowser
import ctypes

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.server import run_server, PORT, get_last_client_seen

EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
]

user32 = ctypes.windll.user32

def is_server_running():
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/heartbeat", timeout=1)
        return req.getcode() == 200
    except Exception:
        return False

def find_edge_binary():
    for p in EDGE_PATHS:
        if os.path.exists(p):
            return p
    return None

def is_app_window_open():
    found = []
    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                val = buff.value
                if 'Pulse' in val or 'Power & battery' in val or '127.0.0.1:5055' in val:
                    found.append(hwnd)
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return len(found) > 0

def start_backend():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to become responsive
    for _ in range(40):
        if is_server_running():
            return True
        time.sleep(0.1)
    return False

def handle_uninstall():
    import winreg
    try:
        # Remove Start Menu shortcut
        start_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
        sm_lnk = os.path.join(start_dir, 'Power & Battery.lnk')
        if os.path.exists(sm_lnk):
            os.remove(sm_lnk)
        
        # Remove Desktop shortcut
        desktop_dir = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        desk_lnk = os.path.join(desktop_dir, 'Power & Battery.lnk')
        if os.path.exists(desk_lnk):
            os.remove(desk_lnk)
            
        # Remove registry uninstall key
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerBattery')
        except:
            pass
            
        # Show prompt via powershell or msgbox
        subprocess.run(['powershell', '-NoProfile', '-Command', 
            "[System.Windows.Forms.MessageBox]::Show('Power & Battery has been successfully uninstalled.', 'Uninstall Complete', 0)"],
            creationflags=0x08000000)
    except Exception as e:
        pass
    sys.exit(0)

def main():
    if '--uninstall' in sys.argv:
        handle_uninstall()

    if not is_server_running():
        start_backend()

    app_url = f"http://127.0.0.1:{PORT}"
    edge_exe = find_edge_binary()

    if edge_exe:
        user_data = os.path.expandvars(r"%TEMP%\WinBatteryStatsApp")
        cmd = [
            edge_exe,
            f"--app={app_url}",
            "--window-size=1180,820",
            f"--user-data-dir={user_data}",
            "--disable-extensions",
            "--disable-component-update",
            "--disable-sync",
            "--enable-gpu-rasterization",
            "--enable-zero-copy",
            "--ignore-gpu-blocklist",
            "--disable-features=Translate,InterestFeedContentSuggestions,OptimizationHints"
        ]
        
        edge_proc = subprocess.Popen(cmd)
        
        # Keep backend alive as long as user is interacting or window is open
        start_time = time.time()
        client_connected_once = False

        while True:
            time.sleep(1.5)
            now = time.time()
            last_seen = get_last_client_seen()

            if now - last_seen < 6:
                client_connected_once = True

            # If Edge process has terminated directly
            if edge_proc.poll() is not None:
                if now - start_time > 10 and (now - last_seen > 6 or not client_connected_once):
                    break

            # If client was connected and hasn't communicated in 15s and window is not visible
            if client_connected_once:
                if (now - last_seen > 15) and not is_app_window_open():
                    break
    else:
        webbrowser.open(app_url)
        while True:
            time.sleep(2)
            if time.time() - get_last_client_seen() > 20:
                break

if __name__ == '__main__':
    main()
