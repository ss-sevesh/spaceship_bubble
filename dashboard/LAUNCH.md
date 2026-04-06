# 🚀 Launch Instructions: Spaceship Bubble Dashboard

Follow these steps to start the professional research dashboard with 3D visualizations and backend connectivity.

### 1. Clear any stuck processes (Optional but recommended)
Run this in any PowerShell window to ensure port 8000 is free:
```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force -ErrorAction SilentlyContinue
```

### 2. Start the Backend (API)
Open a terminal in `C:\Users\11SEV\spaceship_bubble\dashboard` and run:
```powershell
uv run python server.py
```
*Expected output: `INFO: Application startup complete.`*

### 3. Start the Frontend (UI)
Open a second terminal in `C:\Users\11SEV\spaceship_bubble\dashboard` and run:
```powershell
npm run dev
```
*Expected output: `➜ Local: http://localhost:5173/` (or 5174)*

---

### 🛠️ Troubleshooting the "Perfect" Connection
- **System Status Indicator**: Look at the top right of the dashboard. It will show a green **LIVE SYNC** badge when the connection is active, or **LOCAL MODE** when running from static files only.
- **Visualizer**: Switch to "3D View" in the header to see the kinetic material models.
- **Optimization**: The **"Re-Optimize"** button will only be clickable when the **LIVE SYNC** badge is active.

**Dashboard URL:** [http://localhost:5173](http://localhost:5173)
