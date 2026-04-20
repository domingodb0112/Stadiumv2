# Stadium V3 Windows Client - Setup Guide

## ⚠️ Important: Working Directory

**All commands must be executed from the `winClient` folder**, not the parent directory.

```powershell
cd C:\Users\hecto\Documents\Miras Codes\StadiumV3Windows\winClient
```

## 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

Or use the virtual environment:
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run the App

### Option A: Double-click (Windows)
```
Double-click: run.bat
```

### Option B: Command Line (PowerShell)
```powershell
python main.py
```

### Option C: IDE (VSCode/PyCharm)
- **Open Folder:** `C:\Users\hecto\Documents\Miras Codes\StadiumV3Windows\winClient`
- **Set Python Interpreter:** Point to `venv\Scripts\python.exe`
- **Run:** F5 or Ctrl+F5

## 3. Fix Missing Import Errors in IDE

### VSCode:
1. Install extension: **Pylance**
2. Open Command Palette: `Ctrl+Shift+P`
3. Run: **Python: Select Interpreter**
4. Choose: `.venv\Scripts\python.exe`
5. Reload window: `Ctrl+Shift+P` → **Developer: Reload Window**

### PyCharm:
1. File → Settings → Project → Python Interpreter
2. Select: `.\venv\Scripts\python.exe`
3. Apply & OK

## 4. Verify Setup

```powershell
# Check Python version
python --version

# Check installed packages
pip list | grep -E "PyQt5|opencv|mediapipe"
```

## 5. Project Structure

```
winClient/
├── main.py                  # Entry point
├── config.py                # Configuration
├── theme.py                 # AutoZone Brand styles
├── requirements.txt         # Dependencies
├── pyrightconfig.json       # IDE configuration
├── run.bat                  # Windows launcher
├── screens/
│   ├── __init__.py
│   ├── welcome.py
│   ├── player_selection.py
│   ├── camera_preview.py
│   ├── photo_view.py
│   ├── simulation.py
│   └── final_screen.py
├── engine/
│   ├── __init__.py
│   ├── mov_parser.py
│   ├── video_overlay.py
│   └── network_client.py
└── output/                  # Generated photos
```

## 6. Common Issues

### ❌ "Cannot find module 'screens'"
**Solution:** Ensure you're running from `winClient` folder:
```powershell
cd C:\Users\hecto\Documents\Miras Codes\StadiumV3Windows\winClient
python main.py
```

### ❌ "ModuleNotFoundError: No module named 'PyQt5'"
**Solution:** Install dependencies:
```powershell
pip install PyQt5 opencv-python mediapipe requests
```

### ❌ "No module named 'cv2'"
**Solution:**
```powershell
pip install opencv-python
```

### ❌ "Camera not detected"
**Solution:** Check if camera is connected and not in use by another app.

---

**Demo Ready! Launch with:** `python main.py` from `winClient` folder.
