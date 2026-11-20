# Pulse — Power & Battery Intelligence

Pulse is a local Windows battery dashboard with live AC/battery status, Windows battery-report history, process activity, battery health, and power-profile controls.

The product is intentionally conservative: hardware-dependent values are marked estimated or unavailable instead of being presented as measured when Windows does not expose a sensor.

## Features

- Live battery percentage, AC state, charging state, voltage, and time estimate
- Battery-report history for since-charge, 24-hour, and 7-day views
- Persistent local battery samples and charge-cycle transitions
- Foreground process activity attribution, clearly identified as usage-based
- Battery health and OEM battery-care detection where supported
- Windows power settings and validated performance/fan profiles
- Local-only API with per-process mutation token
- Explicit unsupported states for GPU, fan, and thermal providers

## Run

```powershell
cd app
npm install
npm run build
cd ..
python launch.py
```

The launcher starts the local service and opens Microsoft Edge in app mode. Windows is required for the live Win32 and powercfg providers.

## Test

```powershell
python -m unittest discover -s tests -v
cd app
npm run lint
npm run build
```

## Package

```powershell
pyinstaller PowerBattery.spec --noconfirm
pyinstaller PowerBatterySetup.spec --noconfirm
```

The installer provisions the app under `%LOCALAPPDATA%\Programs\PowerBattery` and stores packaged runtime data under `%LOCALAPPDATA%\WindowsBatteryStats`.

See [DOCUMENTATION.md](DOCUMENTATION.md) for the architecture, API, data model, limitations, and operational guidance.
