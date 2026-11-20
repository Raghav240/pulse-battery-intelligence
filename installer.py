import os
import sys
import shutil
import subprocess
import winreg
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = "Pulse - Power & Battery Intelligence"
APP_DIR_NAME = "PowerBattery"
APP_EXE_NAME = "PowerBattery.exe"
VERSION = "2.5.0"

TERMS_AND_CONDITIONS = """PULSE END USER LICENSE AGREEMENT & TERMS OF SERVICE

1. LICENSE GRANT & PRIVACY FIRST
Pulse is a client-side Windows hardware monitoring utility. All battery, thermal, and wattage metrics are read and calculated locally on your device. Pulse collects ZERO telemetric data, transmits no analytics to external servers, and requires no account registration or cloud connectivity.

2. HARDWARE MONITORING & SYSTEM TELEMETRY
Pulse interacts with Windows ACPI Battery subsystems, Windows Management Instrumentation (WMI), and diagnostic hardware controllers (such as HP Adaptive Battery Optimizer, Lenovo Conservation Mode, and ASUS Battery Health Charging) in a safe, read-only manner. Pulse does not flash firmware, overwrite UEFI BIOS memory, or force voltages beyond manufacturer tolerances.

3. INTELLECTUAL PROPERTY & PERMITTED USE
You are granted a personal, non-exclusive, non-transferable license to install and execute Pulse on any compatible Windows PC or laptop. You may use Pulse for personal, educational, or commercial device monitoring.

4. DISCLAIMER OF WARRANTY & LIMITATION OF LIABILITY
Pulse is provided "AS IS", without warranty of any kind, express or implied. In no event shall the authors or developers be held liable for any damages arising from hardware defects, system instability, or inaccurate manufacturer sensor data.

5. ACCEPTANCE OF TERMS
By checking the acceptance box and continuing with this installation, you agree to these Terms and Conditions and acknowledge that Pulse operates as a local device monitor.
"""

def get_install_dir():
    local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
    return os.path.join(local_app_data, 'Programs', APP_DIR_NAME)

def get_start_menu_dir():
    app_data = os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
    return os.path.join(app_data, r'Microsoft\Windows\Start Menu\Programs')

def get_desktop_dir():
    return os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Desktop')

def create_shortcut(target_exe, lnk_path, name):
    try:
        tmp_ps = os.path.join(tempfile.gettempdir(), 'mk_shortcut.ps1')
        script = f'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('{lnk_path}')
$sc.TargetPath = '{target_exe}'
$sc.WorkingDirectory = '{os.path.dirname(target_exe)}'
$sc.Description = '{name}'
$sc.Save()
'''
        with open(tmp_ps, 'w', encoding='utf-8') as f:
            f.write(script)
        subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', tmp_ps], 
                       creationflags=0x08000000 if os.name == 'nt' else 0, 
                       timeout=5)
        if os.path.exists(tmp_ps):
            os.remove(tmp_ps)
        return os.path.exists(lnk_path)
    except Exception:
        return False

def register_uninstaller(install_dir, target_exe):
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerBattery"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Power & Battery")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Pulse Intelligence")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{target_exe}" --uninstall')
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, target_exe)
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception:
        pass

def perform_install(create_desktop=True, create_start=True, launch_after=True):
    install_dir = get_install_dir()
    os.makedirs(install_dir, exist_ok=True)
    target_exe = os.path.join(install_dir, APP_EXE_NAME)

    # Locate source PowerBattery.exe
    source_exe = None
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        embedded = os.path.join(base_dir, APP_EXE_NAME)
        if os.path.exists(embedded):
            source_exe = embedded
    
    if not source_exe or not os.path.exists(source_exe):
        local_cand = os.path.join(os.path.dirname(os.path.abspath(__file__)), APP_EXE_NAME)
        if os.path.exists(local_cand):
            source_exe = local_cand
        else:
            source_exe = os.path.join(os.path.dirname(sys.executable), APP_EXE_NAME)

    if not source_exe or not os.path.exists(source_exe):
        raise FileNotFoundError(f"Could not locate {APP_EXE_NAME} payload.")

    # Terminate running instance if any
    try:
        subprocess.run(['taskkill', '/F', '/IM', APP_EXE_NAME], 
                       creationflags=0x08000000 if os.name == 'nt' else 0, 
                       timeout=3, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception:
        pass

    # Copy binary
    shutil.copy2(source_exe, target_exe)

    # Shortcuts
    if create_start:
        start_dir = get_start_menu_dir()
        create_shortcut(target_exe, os.path.join(start_dir, "Power & Battery.lnk"), "Pulse - Power & Battery Intelligence")

    if create_desktop:
        desk_dir = get_desktop_dir()
        create_shortcut(target_exe, os.path.join(desk_dir, "Power & Battery.lnk"), "Pulse - Power & Battery Intelligence")

    # Windows Apps Registration
    register_uninstaller(install_dir, target_exe)

    # Launch
    if launch_after:
        try:
            subprocess.Popen([target_exe], creationflags=0x08000000 if os.name == 'nt' else 0)
        except Exception:
            pass

    return True

def run_gui_installer():
    root = tk.Tk()
    root.title("Pulse - Power & Battery Setup")
    root.geometry("540x510")
    root.resizable(False, False)

    # Dark Theme matching Windows 11 Acrylic
    bg_color = "#141a29"
    card_bg = "#1e283d"
    fg_color = "#ffffff"
    fg_secondary = "#94a3b8"
    accent = "#38bdf8"
    accent_hover = "#0284c7"
    border_color = "#334155"

    root.configure(bg=bg_color)

    # Header Card
    header = tk.Frame(root, bg=card_bg, height=72)
    header.pack(fill="x", side="top")
    header.pack_propagate(False)

    lbl_title = tk.Label(header, text="Pulse Setup", font=("Segoe UI Variable Display", 16, "bold"), fg=fg_color, bg=card_bg)
    lbl_title.pack(anchor="w", padx=24, pady=(12, 1))

    lbl_sub = tk.Label(header, text=f"Version {VERSION} • Power Intelligence & Hardware Telemetry", 
                       font=("Segoe UI Variable Text", 9), fg=accent, bg=card_bg)
    lbl_sub.pack(anchor="w", padx=24)

    # Body
    body = tk.Frame(root, bg=bg_color, padx=24, pady=14)
    body.pack(fill="both", expand=True)

    lbl_license = tk.Label(body, text="Terms & Conditions and End User License Agreement:", 
                           font=("Segoe UI Variable Text", 9, "bold"), fg=fg_color, bg=bg_color)
    lbl_license.pack(anchor="w", pady=(0, 6))

    # Scrollable T&Cs Text Box
    txt_frame = tk.Frame(body, bg=border_color, padx=1, pady=1)
    txt_frame.pack(fill="both", expand=True, pady=(0, 10))

    txt_terms = tk.Text(txt_frame, wrap="word", height=7, font=("Segoe UI Variable Text", 9),
                        bg="#0f172a", fg="#cbd5e1", insertbackground=fg_color,
                        relief="flat", padx=10, pady=8)
    scrollbar = tk.Scrollbar(txt_frame, command=txt_terms.yview)
    txt_terms.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    txt_terms.pack(side="left", fill="both", expand=True)

    txt_terms.insert("1.0", TERMS_AND_CONDITIONS.strip())
    txt_terms.configure(state="disabled")

    # Agreement Checkbox
    chk_agree_var = tk.BooleanVar(value=True)

    def on_toggle_agree():
        if chk_agree_var.get():
            btn_install.config(state="normal", bg=accent, fg="#000000")
        else:
            btn_install.config(state="disabled", bg="#334155", fg="#64748b")

    chk_agree = tk.Checkbutton(body, text="I accept the Terms and Conditions and License Agreement", 
                               variable=chk_agree_var, command=on_toggle_agree,
                               font=("Segoe UI Variable Text", 9, "bold"),
                               fg=fg_color, bg=bg_color, selectcolor=card_bg, 
                               activebackground=bg_color, activeforeground=fg_color)
    chk_agree.pack(anchor="w", pady=(0, 8))

    # Installation Options
    lbl_opts = tk.Label(body, text="Installation Options:", font=("Segoe UI Variable Text", 9, "bold"), fg=fg_secondary, bg=bg_color)
    lbl_opts.pack(anchor="w", pady=(2, 4))

    opts_frame = tk.Frame(body, bg=bg_color)
    opts_frame.pack(fill="x", pady=(0, 6))

    chk_desktop_var = tk.BooleanVar(value=True)
    chk_desktop = tk.Checkbutton(opts_frame, text="Desktop Shortcut", variable=chk_desktop_var, 
                                 font=("Segoe UI Variable Text", 9),
                                 fg=fg_color, bg=bg_color, selectcolor=card_bg, 
                                 activebackground=bg_color, activeforeground=fg_color)
    chk_desktop.pack(side="left", padx=(0, 20))

    chk_start_var = tk.BooleanVar(value=True)
    chk_start = tk.Checkbutton(opts_frame, text="Start Menu", variable=chk_start_var, 
                               font=("Segoe UI Variable Text", 9),
                               fg=fg_color, bg=bg_color, selectcolor=card_bg, 
                               activebackground=bg_color, activeforeground=fg_color)
    chk_start.pack(side="left", padx=(0, 20))

    chk_launch_var = tk.BooleanVar(value=True)
    chk_launch = tk.Checkbutton(opts_frame, text="Launch Application", variable=chk_launch_var, 
                                font=("Segoe UI Variable Text", 9),
                                fg=fg_color, bg=bg_color, selectcolor=card_bg, 
                                activebackground=bg_color, activeforeground=fg_color)
    chk_launch.pack(side="left")

    # Progress bar
    progress = ttk.Progressbar(body, mode="indeterminate", length=490)

    # Footer Actions
    footer = tk.Frame(root, bg=card_bg, height=56)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)

    lbl_dest = tk.Label(footer, text="Target: %LOCALAPPDATA%\\Programs\\PowerBattery", 
                        font=("Segoe UI Variable Text", 8), fg="#64748b", bg=card_bg)
    lbl_dest.pack(side="left", padx=24)

    def on_install():
        if not chk_agree_var.get():
            messagebox.showwarning("Terms Required", "You must accept the Terms and Conditions to proceed.")
            return

        btn_install.config(state="disabled")
        btn_cancel.config(state="disabled")
        chk_agree.config(state="disabled")
        progress.pack(pady=(6, 0))
        progress.start(10)
        root.update()

        try:
            perform_install(
                create_desktop=chk_desktop_var.get(),
                create_start=chk_start_var.get(),
                launch_after=chk_launch_var.get()
            )
            root.destroy()
        except Exception as e:
            progress.stop()
            progress.pack_forget()
            btn_install.config(state="normal")
            btn_cancel.config(state="normal")
            chk_agree.config(state="normal")
            messagebox.showerror("Installation Error", str(e))

    btn_cancel = tk.Button(footer, text="Cancel", font=("Segoe UI Variable Text", 9), width=10, 
                           bg="#334155", fg=fg_color, relief="flat", 
                           activebackground="#475569", activeforeground=fg_color, command=root.destroy)
    btn_cancel.pack(side="right", padx=(8, 24), pady=12)

    btn_install = tk.Button(footer, text="Install Now", font=("Segoe UI Variable Text", 9, "bold"), width=13, 
                            bg=accent, fg="#000000", relief="flat", 
                            activebackground=accent_hover, activeforeground="#000000", command=on_install)
    btn_install.pack(side="right", pady=12)

    root.mainloop()

if __name__ == "__main__":
    args_lower = [a.lower() for a in sys.argv]
    if "/s" in args_lower or "--silent" in args_lower:
        try:
            perform_install(create_desktop=True, create_start=True, launch_after=False)
            sys.exit(0)
        except Exception as e:
            try:
                with open(os.path.join(tempfile.gettempdir(), 'pulse_install_err.log'), 'w') as f:
                    f.write(str(e))
            except:
                pass
            sys.exit(1)
    else:
        run_gui_installer()
