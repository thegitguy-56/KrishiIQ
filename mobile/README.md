# KrishiIQ Mobile App (Flutter)

## Prerequisites

- **Flutter 3.44** at `C:\Users\surya.gollavilli\flutter` (added to user PATH by setup script)
- **Windows Developer Mode** on (Settings → System → For developers) — required for plugin symlinks
- **Android Studio** (optional, for emulator) — install SDK cmdline-tools and run `flutter doctor --android-licenses`
- Backend API on port **8001**

Platform folders (`android/`, `windows/`, etc.) are generated; run setup once if missing.

## Quick setup

```powershell
cd ..\scripts
.\setup-flutter.ps1
```

## `flutter` not recognized?

Your terminal was opened **before** Flutter was added to PATH. Use **one** of these:

**Option A — reload PATH in this window (fastest):**

```powershell
cd mobile
. .\flutter-env.ps1
flutter pub get
flutter run -d windows
```

**Option B — close this terminal, open a new PowerShell**, then `flutter` works globally.

**Option C — full path (no PATH needed):**

```powershell
& "C:\Users\surya.gollavilli\flutter\bin\flutter.bat" pub get
& "C:\Users\surya.gollavilli\flutter\bin\flutter.bat" run -d windows
```

**Option D — one script:**

```powershell
cd mobile
.\run.ps1
```

## Run the app

```powershell
cd mobile
. .\flutter-env.ps1
flutter devices
flutter run -d windows    # desktop (no emulator needed)
flutter run -d chrome     # web preview
flutter run               # first Android device/emulator
```

## API URL (`lib/config/app_config.dart`)

| Device | baseUrl |
|--------|---------|
| Android emulator | `http://10.0.2.2:8001/api/v1` |
| Physical phone (same Wi‑Fi) | `http://YOUR_PC_IP:8001/api/v1` |
| Windows desktop | `http://127.0.0.1:8001/api/v1` |

## Test farmer account

- Phone: `9000000002`
- Password: `farmer123`
- Registration: name, email, mobile, password, district (no OTP)

## Features

- Register / Login (farmer only)
- Bottom nav: Home, Advisory, Sensors, History, Profile
- AI disease detection (camera)
- AI chat assistant
- Voice advisories (TTS)
- Farm map
