# Pulse — Power & Battery Intelligence

Pulse is a local Windows desktop dashboard for battery status, battery-report history, process activity, and Windows power settings.

## Product status

Pulse is designed to be honest about hardware support. Windows exposes reliable battery percentage, AC state, voltage, and some rate information, but temperature, fan RPM, GPU power, and factory battery capacity are hardware/vendor dependent. When a provider is unavailable, Pulse displays `N/A` instead of inventing a measurement.

## Architecture

```text
Edge app window / Vite React UI
              |
       127.0.0.1:5055
              |
Python threaded HTTP API
       |              |
 Win32/powercfg     SQLite
       |
 Windows hardware providers
```

### Frontend

- React 19 and Vite
- Battery & Performance, Battery Health, Usage History, and Settings views
- Backend-configured live polling
- Loading and unsupported states for unavailable telemetry

### Backend

- `GetSystemPowerStatus` for AC, battery percentage, and charging state
- `powercfg /batteryreport /xml` for Windows history and capacity data
- `CallNtPowerInformation` for battery rate information when supported
- `nvidia-smi` only when an NVIDIA GPU is present
- `psutil` for CPU utilization/frequency
- SQLite for battery samples, app sessions, and charge cycles

## Data model

`battery_samples` stores timestamped percentage, charging state, remaining time, voltage, power rate, and optional sensor readings.

`app_sessions` stores foreground activity intervals and process metadata. App percentages are usage-based estimates, not direct electrical energy measurements.

`charge_cycles` stores transitions from AC to battery and back to AC.

The database is stored beside the source backend during development and under `%LOCALAPPDATA%\WindowsBatteryStats` for packaged builds.

## API

All endpoints are local-only and bind to `127.0.0.1:5055`.

| Endpoint | Method | Purpose |
|---|---:|---|
| `/api/session` | GET | Gets the per-process token used for mutating requests |
| `/api/heartbeat` | GET | Liveness check |
| `/api/settings` | GET/POST | Read or validate preferences |
| `/api/battery/status` | GET | Live battery and hardware payload |
| `/api/battery/stats?mode=since_charge\|today\|week` | GET | Battery history and graph points |
| `/api/battery/specs` | GET | Parsed battery report specifications |
| `/api/hardware/telemetry` | GET | Current hardware provider payload |
| `/api/apps/usage` | GET | Usage-based process attribution |
| `/api/action/open_windows_settings` | POST | Opens Windows power settings |
| `/api/action/set_fan_profile` | POST | Applies a validated cooling policy |
| `/api/action/set_power_mode` | POST | Applies a validated Windows power scheme |
| `/api/action/refresh` | POST | Refreshes the battery report |

POST requests require the `X-Pulse-Token` header returned by `/api/session`.

## Run from source

```powershell
cd app
npm install
npm run build
cd ..
python launch.py
```

The backend serves `app/dist` automatically. The application requires Windows because the live providers use Win32 and Windows commands.

## Build packaged executables

```powershell
pyinstaller PowerBattery.spec --noconfirm
pyinstaller PowerBatterySetup.spec --noconfirm
```

The installer targets `%LOCALAPPDATA%\Programs\PowerBattery`, creates optional shortcuts, and registers a per-user uninstaller.

## Verification

```powershell
python -m unittest discover -s tests -v
```

Run frontend checks from `app` with `npm run lint` and `npm run build`.

## Privacy and limitations

- No cloud service or analytics endpoint is used.
- Process names, window activity, and battery samples are stored locally.
- Power and temperature values may be estimates or unavailable depending on hardware.
- OEM battery-care detection is best-effort and is not firmware certification.
- The application does not physically enforce a charge limit; it only alerts or opens Windows/OEM settings.
