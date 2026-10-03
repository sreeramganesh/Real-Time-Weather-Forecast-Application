# Atmosphere - State-of-the-Art Desktop Weather Application

A complete, modern Python weather intelligence suite featuring a **high-DPI Dark Mode Desktop GUI** and an **interactive colorized terminal CLI**, powered by the [OpenWeatherMap API](https://openweathermap.org/api).

---

## 🌟 Visual & Architectural Highlights

### 🖥️ Desktop GUI (`weather_gui.py`)
- **Native Windows High-DPI Support**: Automatically enables process DPI awareness (`shcore.SetProcessDpiAwareness(1)`) so typography, icons, and layout edges are razor-sharp on high-resolution monitors and 125%/150% Windows scaling.
- **Native Dark Title Bar**: Hooks directly into Windows DWM (`DwmSetWindowAttribute`) to theme the OS window frame in deep dark mode.
- **Ultra-HD Weather Icons**: Downloads `@4x` high-resolution weather graphics from OpenWeatherMap, scaled down with Pillow Lanczos resampling for crisp, anti-aliased visual fidelity.
- **Visual Progress Meters**: Mini canvas-based progress bars for **Humidity** and **Cloud Cover**.
- **Dynamic Weather Theming**: Hero card border and badges shift accent color dynamically:
  - ☀️ **Clear / Sunny**: Warm Amber Gold (`#f59e0b`)
  - 🌧️ **Rain / Storm**: Electric Indigo (`#818cf8`)
  - ❄️ **Snow**: Frost Cyan (`#06b6d4`)
  - ☁️ **Clouds**: Sky Blue (`#38bdf8`)
- **Interactive Micro-Animations**: Cards and buttons subtly brighten and highlight when hovered over with the mouse.
- **⏱️ Upcoming Hours Timeline**: 6 horizontal cards showing upcoming 3-hour forecasts with icons, temps, and rain probability.
- **📅 5-Day Extended Outlook**: Daily summary cards with Min / Max temperature spans and precipitation chance.
- **📊 Detailed Conditions Grid**:
  - 💧 **Humidity**: Relative moisture % + visual progress bar + dew point
  - 💨 **Wind**: Speed, 16-point compass direction (e.g. `2.5 m/s (ENE)`), and wind gust speeds
  - ⏱️ **Pressure**: Sea-level pressure (`hPa`) with atmospheric condition rating
  - 👁️ **Visibility**: Sight distance in kilometers or miles with clarity rating
  - ☁️ **Cloud Cover**: Sky coverage % + visual progress bar
  - 🌅 **Sun Schedule**: Exact local sunrise and sunset + calculated total daylight duration
- **Interactive Controls**:
  - Search field with clear (✕) button and keyboard shortcut (<kbd>Enter</kbd>).
  - Instant unit toggle pill (`°C` / `°F`).
  - Refresh button (`🔄`).
  - Quick-pick city chips for one-click weather lookups.
- **Non-Blocking Multithreading**: All network queries run on background daemon threads so the UI never lags or freezes.

---

### 📟 Terminal CLI (`weather_app.py`)
- Continuous interactive query loop (`q` or `exit` to quit).
- Dynamic temperature color grading using `colorama`.
- Local sunrise and sunset calculations.
- Formatted 5-day daily forecast table.
- Windows `cp1252` encoding protection.

---

## 📦 Installation & Setup

1. **Navigate to the directory:**
   ```bash
   cd "e:/Project/Python Project/python intership/Weather app"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Configure your custom API key:**
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - Add your OpenWeatherMap key:
     ```env
     OPENWEATHER_API_KEY=your_actual_api_key_here
     ```

---

## 🚀 Running the Application

### 1. Launch the Desktop GUI
```bash
python weather_gui.py
```

### 2. Launch the Interactive CLI
```bash
python weather_app.py
```

---

## 📂 Project Architecture
```
Weather app/
├── .env.example       # Template for custom API keys
├── .gitignore         # Git ignore rules (.env, __pycache__)
├── requirements.txt   # Dependencies (requests, python-dotenv, colorama, Pillow)
├── weather_gui.py     # Modern Tkinter Desktop GUI application
├── weather_app.py     # Interactive CLI application with 5-day forecast
└── README.md          # Project documentation
```
