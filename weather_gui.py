"""
Atmosphere - State-of-the-Art Desktop Weather Application
Features High-DPI Awareness, Dark Window Framing, Real-Time Weather,
Hourly Timeline, 5-Day Extended Outlook, and Visual Environmental Meters.
"""

import io
import os
import sys
import threading
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import tkinter as tk
from tkinter import font as tkfont
import requests
from dotenv import load_dotenv
from PIL import Image, ImageTk

# Enable Windows High-DPI Awareness for razor-sharp typography & icons
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

# Load environment configuration
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Premium Obsidian & Slate Theme
BG_MAIN = "#0b0f19"              # Deep obsidian background
BG_SURFACE = "#111827"           # Card surface layer
BG_SURFACE_HOVER = "#182236"     # Card surface hover
BG_INPUT = "#0f172a"             # Input field background
BORDER_SUBTLE = "#1f293d"        # Subtle card boundary
BORDER_HOVER = "#38bdf8"         # Interactive hover border

# Dynamic Weather Accents
ACCENT_AMBER = "#f59e0b"         # Sun / Clear
ACCENT_SKY = "#38bdf8"           # Clouds / Atmospheric
ACCENT_INDIGO = "#818cf8"        # Rain / Storm
ACCENT_CYAN = "#06b6d4"          # Snow / Cold
ACCENT_EMERALD = "#10b981"       # Mint green success
ACCENT_ROSE = "#f43f5e"          # Error alert

# Typography Colors
TEXT_PRIMARY = "#f8fafc"         # Bright white
TEXT_SECONDARY = "#94a3b8"       # Slate gray
TEXT_MUTED = "#64748b"           # Dark muted gray

# Weather Emoji Fallbacks
EMOJI_FALLBACK = {
    "01d": "☀️", "01n": "🌙",
    "02d": "⛅", "02n": "☁️",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️",
}


def deg_to_compass(deg) -> str:
    """Convert wind degrees to 16-point compass directions."""
    try:
        val = int((float(deg) / 22.5) + 0.5)
        points = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        return points[(val % 16)]
    except (ValueError, TypeError):
        return "N/A"


class WeatherAppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Atmosphere | Modern Weather Intelligence")
        self.geometry("1020x840")
        self.minsize(920, 720)
        self.configure(bg=BG_MAIN)

        # Apply dark title bar on Windows 10/11
        if sys.platform.startswith("win"):
            self.after(10, self._apply_dark_titlebar)

        # State Variables
        self.current_city = "London"
        self.units = "metric"  # "metric" (°C, m/s, km) or "imperial" (°F, mph, mi)
        self.recent_searches = ["Ooty", "Mumbai", "London", "Tokyo", "New York", "Paris"]
        self.icon_cache = {}
        self.hourly_cards = []
        self.forecast_cards = []

        self._init_fonts()
        self._build_ui()

        # Load default city on launch
        self.after(200, lambda: self.search_city(self.current_city))

    def _apply_dark_titlebar(self):
        """Enable native Windows 10/11 dark title bar."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value)
            )
        except Exception:
            pass

    def _init_fonts(self):
        """Configure responsive, modern typography."""
        family = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"
        self.font_logo = tkfont.Font(family=family, size=15, weight="bold")
        self.font_temp_hero = tkfont.Font(family=family, size=54, weight="bold")
        self.font_city = tkfont.Font(family=family, size=24, weight="bold")
        self.font_section = tkfont.Font(family=family, size=12, weight="bold")
        self.font_body = tkfont.Font(family=family, size=10)
        self.font_bold = tkfont.Font(family=family, size=10, weight="bold")
        self.font_metric_val = tkfont.Font(family=family, size=14, weight="bold")
        self.font_small = tkfont.Font(family=family, size=9)

    def _build_ui(self):
        """Construct the visual layout hierarchy."""
        # Fixed Top Navigation Bar
        self.header_frame = tk.Frame(self, bg=BG_MAIN, padx=26, pady=16)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self._build_header()

        # Scrollable Canvas Viewport for main dashboard
        self.canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.content_frame = tk.Frame(self.canvas, bg=BG_MAIN, padx=26, pady=4)

        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Dynamic Canvas width sync
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width)
        )

        # Mouse wheel support
        self.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Build Dashboard Widgets
        self._build_quick_chips_bar()
        self._build_hero_section()
        self._build_hourly_section()
        self._build_forecast_section()
        self._build_metrics_grid()

    def _build_header(self):
        """Top navigation with search, unit selector, and refresh button."""
        # Logo & Subtitle
        brand_box = tk.Frame(self.header_frame, bg=BG_MAIN)
        brand_box.pack(side=tk.LEFT)

        tk.Label(
            brand_box,
            text="🌦️ Atmosphere",
            font=self.font_logo,
            fg=ACCENT_SKY,
            bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            brand_box,
            text="Real-Time Meteorological Intelligence",
            font=self.font_small,
            fg=TEXT_SECONDARY,
            bg=BG_MAIN,
        ).pack(anchor="w")

        # Right Action Bar
        actions_box = tk.Frame(self.header_frame, bg=BG_MAIN)
        actions_box.pack(side=tk.RIGHT)

        # Modern Search Pill
        search_pill = tk.Frame(
            actions_box,
            bg=BG_INPUT,
            highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
            padx=4,
            pady=3,
        )
        search_pill.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(search_pill, text="🔍", font=self.font_body, fg=TEXT_MUTED, bg=BG_INPUT).pack(side=tk.LEFT, padx=(6, 4))

        self.search_entry = tk.Entry(
            search_pill,
            font=self.font_body,
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief=tk.FLAT,
            width=22,
        )
        self.search_entry.pack(side=tk.LEFT, padx=4, ipady=3)
        self.search_entry.bind("<Return>", lambda e: self.on_search())

        # Clear Entry Button (✕)
        self.btn_clear = tk.Button(
            search_pill,
            text="✕",
            font=self.font_small,
            bg=BG_INPUT,
            fg=TEXT_MUTED,
            activebackground=BG_INPUT,
            activeforeground=TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=4,
            command=lambda: self.search_entry.delete(0, tk.END),
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_search = tk.Button(
            search_pill,
            text="Search",
            font=self.font_bold,
            bg="#0284c7",
            fg=TEXT_PRIMARY,
            activebackground="#0ea5e9",
            activeforeground=TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=2,
            command=self.on_search,
        )
        self.btn_search.pack(side=tk.LEFT)

        # Refresh Button
        self.btn_refresh = tk.Button(
            actions_box,
            text="🔄 Refresh",
            font=self.font_bold,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            activebackground=BG_SURFACE_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief=tk.FLAT,
            highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
            cursor="hand2",
            padx=10,
            pady=4,
            command=lambda: self.search_city(self.current_city),
        )
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 10))

        # Unit Selector Pill (°C / °F)
        unit_pill = tk.Frame(
            actions_box,
            bg=BG_SURFACE,
            highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
            padx=2,
            pady=2,
        )
        unit_pill.pack(side=tk.LEFT)

        self.btn_metric = tk.Button(
            unit_pill,
            text="°C",
            font=self.font_bold,
            bg="#0284c7",
            fg=TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=2,
            command=lambda: self.set_units("metric"),
        )
        self.btn_metric.pack(side=tk.LEFT)

        self.btn_imperial = tk.Button(
            unit_pill,
            text="°F",
            font=self.font_bold,
            bg=BG_SURFACE,
            fg=TEXT_MUTED,
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=2,
            command=lambda: self.set_units("imperial"),
        )
        self.btn_imperial.pack(side=tk.LEFT)

    def _build_quick_chips_bar(self):
        """Render recent city tags for instant lookup."""
        self.chips_frame = tk.Frame(self.content_frame, bg=BG_MAIN)
        self.chips_frame.pack(fill=tk.X, pady=(0, 8))
        self._refresh_chips()

        self.lbl_status = tk.Label(
            self.content_frame,
            text="",
            font=self.font_body,
            fg=ACCENT_SKY,
            bg=BG_MAIN,
        )
        self.lbl_status.pack(anchor="w", pady=(0, 8))

    def _refresh_chips(self):
        """Redraw city chips when recent search list changes."""
        for widget in self.chips_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.chips_frame,
            text="Quick Cities:",
            font=self.font_small,
            fg=TEXT_MUTED,
            bg=BG_MAIN,
        ).pack(side=tk.LEFT, padx=(2, 6))

        for city in self.recent_searches:
            btn = tk.Button(
                self.chips_frame,
                text=city,
                font=self.font_small,
                bg=BG_SURFACE,
                fg=TEXT_SECONDARY,
                activebackground=BG_SURFACE_HOVER,
                activeforeground=TEXT_PRIMARY,
                relief=tk.FLAT,
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda c=city: self.search_city(c),
            )
            btn.pack(side=tk.LEFT, padx=3)
            self._add_hover_effect(btn, BG_SURFACE, BG_SURFACE_HOVER)

    def _build_hero_card(self):
        """Construct the prominent weather hero banner with dynamic accent."""
        self.hero_outer = tk.Frame(
            self.content_frame,
            bg=ACCENT_SKY,
            padx=1,
            pady=1,
        )
        self.hero_outer.pack(fill=tk.X, pady=(0, 16))

        self.hero_card = tk.Frame(
            self.hero_outer,
            bg=BG_SURFACE,
            padx=24,
            pady=20,
        )
        self.hero_card.pack(fill=tk.BOTH, expand=True)

        # Left Column: Location, Local Time, Condition Badge
        hero_left = tk.Frame(self.hero_card, bg=BG_SURFACE)
        hero_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.lbl_city = tk.Label(
            hero_left,
            text="Loading Weather...",
            font=self.font_city,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
        )
        self.lbl_city.pack(anchor="w")

        self.lbl_time = tk.Label(
            hero_left,
            text="--",
            font=self.font_body,
            fg=TEXT_SECONDARY,
            bg=BG_SURFACE,
        )
        self.lbl_time.pack(anchor="w", pady=(3, 10))

        badge_row = tk.Frame(hero_left, bg=BG_SURFACE)
        badge_row.pack(anchor="w")

        self.lbl_badge = tk.Label(
            badge_row,
            text="--",
            font=self.font_bold,
            fg=ACCENT_SKY,
            bg="#0d1526",
            padx=12,
            pady=5,
        )
        self.lbl_badge.pack(side=tk.LEFT)

        self.lbl_hilo = tk.Label(
            badge_row,
            text="H: -- • L: --",
            font=self.font_small,
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
        )
        self.lbl_hilo.pack(side=tk.LEFT, padx=(12, 0))

        # Right Column: High-Res Weather Icon & Large Temperature
        hero_right = tk.Frame(self.hero_card, bg=BG_SURFACE)
        hero_right.pack(side=tk.RIGHT)

        self.lbl_hero_icon = tk.Label(
            hero_right,
            text="🌦️",
            font=tkfont.Font(size=46),
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
        )
        self.lbl_hero_icon.pack(side=tk.LEFT, padx=(0, 16))

        hero_temp_box = tk.Frame(hero_right, bg=BG_SURFACE)
        hero_temp_box.pack(side=tk.LEFT)

        self.lbl_temp = tk.Label(
            hero_temp_box,
            text="--°",
            font=self.font_temp_hero,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
        )
        self.lbl_temp.pack(anchor="e")

        self.lbl_feels = tk.Label(
            hero_temp_box,
            text="Feels like: --°",
            font=self.font_small,
            fg=TEXT_SECONDARY,
            bg=BG_SURFACE,
        )
        self.lbl_feels.pack(anchor="e")

    def _build_hero_section(self):
        """Wrapper for hero card initialization."""
        self._build_hero_card()

    def _build_hourly_section(self):
        """Construct the next 24-hour horizontal forecast timeline."""
        header = tk.Frame(self.content_frame, bg=BG_MAIN)
        header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            header,
            text="⏱️ Upcoming Hours (Today's Timeline)",
            font=self.font_section,
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        ).pack(side=tk.LEFT)

        hourly_box = tk.Frame(self.content_frame, bg=BG_MAIN)
        hourly_box.pack(fill=tk.X, pady=(0, 16))
        hourly_box.columnconfigure(tuple(range(6)), weight=1, uniform="h_cols")

        for col in range(6):
            card = tk.Frame(
                hourly_box,
                bg=BG_SURFACE,
                highlightbackground=BORDER_SUBTLE,
                highlightthickness=1,
                padx=6,
                pady=10,
            )
            card.grid(row=0, column=col, sticky="nsew", padx=3)

            lbl_time = tk.Label(card, text="--", font=self.font_bold, fg=TEXT_SECONDARY, bg=BG_SURFACE)
            lbl_time.pack(pady=(0, 2))

            lbl_icon = tk.Label(card, text="☁️", font=tkfont.Font(size=18), bg=BG_SURFACE, fg=TEXT_PRIMARY)
            lbl_icon.pack(pady=2)

            lbl_temp = tk.Label(card, text="--°", font=self.font_bold, fg=TEXT_PRIMARY, bg=BG_SURFACE)
            lbl_temp.pack(pady=2)

            lbl_rain = tk.Label(card, text="-", font=self.font_small, fg=ACCENT_SKY, bg=BG_SURFACE)
            lbl_rain.pack(pady=(2, 0))

            self._add_hover_effect(card, BG_SURFACE, BG_SURFACE_HOVER)

            self.hourly_cards.append({
                "time": lbl_time,
                "icon": lbl_icon,
                "temp": lbl_temp,
                "rain": lbl_rain,
            })

    def _build_forecast_section(self):
        """Construct 5-day daily forecast outlook cards."""
        header = tk.Frame(self.content_frame, bg=BG_MAIN)
        header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            header,
            text="📅 5-Day Extended Outlook",
            font=self.font_section,
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        ).pack(side=tk.LEFT)

        forecast_box = tk.Frame(self.content_frame, bg=BG_MAIN)
        forecast_box.pack(fill=tk.X, pady=(0, 16))
        forecast_box.columnconfigure(tuple(range(5)), weight=1, uniform="fc_cols")

        for col in range(5):
            card = tk.Frame(
                forecast_box,
                bg=BG_SURFACE,
                highlightbackground=BORDER_SUBTLE,
                highlightthickness=1,
                padx=8,
                pady=12,
            )
            card.grid(row=0, column=col, sticky="nsew", padx=3)

            lbl_day = tk.Label(card, text="--", font=self.font_bold, fg=TEXT_PRIMARY, bg=BG_SURFACE)
            lbl_day.pack(pady=(0, 4))

            lbl_icon = tk.Label(card, text="⛅", font=tkfont.Font(size=22), fg=TEXT_PRIMARY, bg=BG_SURFACE)
            lbl_icon.pack(pady=2)

            lbl_temp = tk.Label(card, text="-- / --", font=self.font_bold, fg=ACCENT_CYAN, bg=BG_SURFACE)
            lbl_temp.pack(pady=2)

            lbl_rain = tk.Label(card, text="💧 -", font=self.font_small, fg=TEXT_SECONDARY, bg=BG_SURFACE)
            lbl_rain.pack(pady=2)

            lbl_cond = tk.Label(
                card,
                text="--",
                font=self.font_small,
                fg=TEXT_MUTED,
                bg=BG_SURFACE,
                wraplength=120,
            )
            lbl_cond.pack(pady=(2, 0))

            self._add_hover_effect(card, BG_SURFACE, BG_SURFACE_HOVER)

            self.forecast_cards.append({
                "day": lbl_day,
                "icon": lbl_icon,
                "temp": lbl_temp,
                "rain": lbl_rain,
                "cond": lbl_cond,
            })

    def _build_metrics_grid(self):
        """Construct 6 detailed environmental tiles with visual gauges."""
        header = tk.Frame(self.content_frame, bg=BG_MAIN)
        header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            header,
            text="📊 Environmental Conditions & Atmospheric Data",
            font=self.font_section,
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        ).pack(side=tk.LEFT)

        grid = tk.Frame(self.content_frame, bg=BG_MAIN)
        grid.pack(fill=tk.X, pady=(0, 20))
        grid.columnconfigure((0, 1, 2), weight=1, uniform="m_cols")

        # Row 1
        self.tile_humidity = self._create_metric_card(
            grid, 0, 0, "💧 Humidity", "--%", "Relative moisture in air", has_bar=True
        )
        self.tile_wind = self._create_metric_card(
            grid, 0, 1, "💨 Wind", "--", "Speed, compass & gusts"
        )
        self.tile_pressure = self._create_metric_card(
            grid, 0, 2, "⏱️ Pressure", "-- hPa", "Sea-level atmospheric pressure"
        )

        # Row 2
        self.tile_visibility = self._create_metric_card(
            grid, 1, 0, "👁️ Visibility", "--", "Clear atmospheric sight distance"
        )
        self.tile_clouds = self._create_metric_card(
            grid, 1, 1, "☁️ Cloud Cover", "--%", "Sky coverage fraction", has_bar=True
        )
        self.tile_sun = self._create_metric_card(
            grid, 1, 2, "🌅 Sun Schedule", "Rise: --  •  Set: --", "Daylight span & solar timings"
        )

    def _create_metric_card(self, parent, row, col, title, initial_val, subtitle="", has_bar=False):
        """Helper to create a detailed environmental metric tile with optional progress bar."""
        frame = tk.Frame(
            parent,
            bg=BG_SURFACE,
            highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        frame.grid(row=row, column=col, sticky="nsew", padx=3, pady=4)

        tk.Label(frame, text=title, font=self.font_small, fg=TEXT_MUTED, bg=BG_SURFACE).pack(anchor="w")

        val_lbl = tk.Label(
            frame,
            text=initial_val,
            font=self.font_metric_val,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            justify=tk.LEFT,
        )
        val_lbl.pack(anchor="w", pady=(3, 2))

        bar_canvas = None
        if has_bar:
            bar_canvas = tk.Canvas(frame, height=5, width=160, bg=BG_INPUT, highlightthickness=0)
            bar_canvas.pack(anchor="w", pady=(2, 4))

        sub_lbl = None
        if subtitle:
            sub_lbl = tk.Label(frame, text=subtitle, font=self.font_small, fg=TEXT_MUTED, bg=BG_SURFACE)
            sub_lbl.pack(anchor="w")

        self._add_hover_effect(frame, BG_SURFACE, BG_SURFACE_HOVER)

        return {"val": val_lbl, "sub": sub_lbl, "bar": bar_canvas}

    def _add_hover_effect(self, widget, normal_bg, hover_bg):
        """Add subtle interactive hover highlights."""
        def on_enter(e):
            try:
                widget.config(bg=hover_bg)
                for child in widget.winfo_children():
                    if child.winfo_class() == "Label":
                        child.config(bg=hover_bg)
            except Exception:
                pass

        def on_leave(e):
            try:
                widget.config(bg=normal_bg)
                for child in widget.winfo_children():
                    if child.winfo_class() == "Label":
                        child.config(bg=normal_bg)
            except Exception:
                pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def set_units(self, unit_system: str):
        """Toggle between metric (°C) and imperial (°F)."""
        if self.units == unit_system:
            return
        self.units = unit_system

        if self.units == "metric":
            self.btn_metric.config(bg="#0284c7", fg=TEXT_PRIMARY)
            self.btn_imperial.config(bg=BG_SURFACE, fg=TEXT_MUTED)
        else:
            self.btn_imperial.config(bg="#0284c7", fg=TEXT_PRIMARY)
            self.btn_metric.config(bg=BG_SURFACE, fg=TEXT_MUTED)

        # Refetch with new unit parameters
        self.search_city(self.current_city)

    def on_search(self):
        """Execute search when button clicked or Enter pressed."""
        city = self.search_entry.get().strip()
        if not city:
            self.set_status("Please enter a city name to search.", is_error=True)
            return
        self.search_city(city)

    def search_city(self, city: str):
        """Launch background worker thread for non-blocking fetch."""
        self.set_status(f"Fetching weather intelligence for {city}...", is_error=False)
        self.btn_search.config(state=tk.DISABLED, text="...")
        self.btn_refresh.config(state=tk.DISABLED)

        threading.Thread(target=self._worker_fetch, args=(city,), daemon=True).start()

    def _worker_fetch(self, city: str):
        """Query REST APIs concurrently."""
        try:
            # 1. Fetch Current Weather
            weather_params = {"q": city, "appid": API_KEY, "units": self.units}
            res_w = requests.get(BASE_URL, params=weather_params, timeout=10)

            if res_w.status_code == 404:
                self.after(0, self.set_status, f"City '{city}' not found. Please verify spelling.", True)
                return
            elif res_w.status_code == 401:
                self.after(0, self.set_status, "Invalid API key. Check credentials.", True)
                return
            elif res_w.status_code != 200:
                self.after(0, self.set_status, f"Error {res_w.status_code}: Unable to fetch data.", True)
                return

            current_data = res_w.json()

            # 2. Fetch 5-Day Forecast
            forecast_params = {"q": city, "appid": API_KEY, "units": self.units}
            res_f = requests.get(FORECAST_URL, params=forecast_params, timeout=10)
            forecast_data = res_f.json() if res_f.status_code == 200 else None

            # 3. Fetch High-Res 4x Hero Icon
            icon_code = current_data.get("weather", [{}])[0].get("icon", "")
            hero_icon = self._get_icon_image(icon_code, size=(110, 110), use_4x=True)

            # Schedule UI render on main thread
            self.after(0, self._render_dashboard_data, city, current_data, forecast_data, hero_icon)

        except requests.Timeout:
            self.after(0, self.set_status, "Connection timed out. Please try again.", True)
        except requests.ConnectionError:
            self.after(0, self.set_status, "Network connection error. Check your internet connection.", True)
        except Exception as e:
            self.after(0, self.set_status, f"Error: {e}", True)
        finally:
            self.after(0, lambda: self.btn_search.config(state=tk.NORMAL, text="Search"))
            self.after(0, lambda: self.btn_refresh.config(state=tk.NORMAL))

    def _get_icon_image(self, icon_code: str, size=(50, 50), use_4x=False):
        """Retrieve, cache, and high-quality Lanczos scale weather icons."""
        if not icon_code:
            return None
        cache_key = f"{icon_code}_{size[0]}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        try:
            scale_str = "@4x.png" if use_4x else "@2x.png"
            url = f"https://openweathermap.org/img/wn/{icon_code}{scale_str}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                img = Image.open(io.BytesIO(resp.content))
                img = img.resize(size, Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.icon_cache[cache_key] = tk_img
                return tk_img
        except Exception:
            pass
        return None

    def _render_dashboard_data(self, searched_city: str, current_data: dict, forecast_data: dict, hero_icon):
        """Render all dashboard components with parsed data."""
        self.set_status("")

        city_name = current_data.get("name", searched_city)
        country = current_data.get("sys", {}).get("country", "")
        self.current_city = city_name
        self.lbl_city.config(text=f"📍 {city_name}, {country}" if country else f"📍 {city_name}")

        # Update Recent Search List
        if city_name not in self.recent_searches:
            self.recent_searches.insert(0, city_name)
            self.recent_searches = self.recent_searches[:6]
            self._refresh_chips()

        # Destination City Local Clock
        tz_offset = current_data.get("timezone", 0)
        city_tz = timezone(timedelta(seconds=tz_offset))
        now_city = datetime.now(tz=city_tz)
        self.lbl_time.config(text=now_city.strftime("🕐 %A, %B %d, %Y  •  %I:%M %p Local Time"))

        # Units and Values
        temp_unit = "°C" if self.units == "metric" else "°F"
        speed_unit = "m/s" if self.units == "metric" else "mph"
        dist_unit = "km" if self.units == "metric" else "mi"

        main_info = current_data.get("main", {})
        temp = main_info.get("temp", 0)
        feels_like = main_info.get("feels_like", 0)
        temp_min = main_info.get("temp_min", temp)
        temp_max = main_info.get("temp_max", temp)

        self.lbl_temp.config(text=f"{temp:.1f}{temp_unit}")
        self.lbl_feels.config(text=f"Feels like: {feels_like:.1f}{temp_unit}")
        self.lbl_hilo.config(text=f"High: {temp_max:.1f}{temp_unit}  •  Low: {temp_min:.1f}{temp_unit}")

        weather_list = current_data.get("weather", [])
        desc = weather_list[0].get("description", "N/A").title() if weather_list else "N/A"
        icon_code = weather_list[0].get("icon", "") if weather_list else ""
        self.lbl_badge.config(text=desc)

        # Dynamic Weather Theme Accent
        weather_main = weather_list[0].get("main", "").lower() if weather_list else ""
        if "clear" in weather_main:
            accent = ACCENT_AMBER
        elif "rain" in weather_main or "drizzle" in weather_main or "thunder" in weather_main:
            accent = ACCENT_INDIGO
        elif "snow" in weather_main:
            accent = ACCENT_CYAN
        else:
            accent = ACCENT_SKY

        self.hero_outer.config(bg=accent)
        self.lbl_badge.config(fg=accent)

        # High-Res Hero Icon
        if hero_icon:
            self.lbl_hero_icon.config(image=hero_icon, text="")
            self.lbl_hero_icon.image = hero_icon
        else:
            self.lbl_hero_icon.config(image="", text=EMOJI_FALLBACK.get(icon_code, "🌦️"))

        # 1. Humidity Tile
        humidity = main_info.get("humidity", 0)
        self.tile_humidity["val"].config(text=f"{humidity}%")
        self._draw_progress_bar(self.tile_humidity["bar"], humidity, 100, ACCENT_SKY)

        # 2. Wind Tile
        wind_info = current_data.get("wind", {})
        wind_speed = wind_info.get("speed", 0)
        wind_deg = wind_info.get("deg")
        compass = deg_to_compass(wind_deg) if wind_deg is not None else "--"
        gust = wind_info.get("gust")
        gust_str = f"Gusts: {gust} {speed_unit}" if gust else "Stable breeze"
        self.tile_wind["val"].config(text=f"{wind_speed} {speed_unit}  ({compass})")
        if self.tile_wind["sub"]:
            self.tile_wind["sub"].config(text=f"Direction: {wind_deg}° • {gust_str}")

        # 3. Pressure Tile
        pressure = main_info.get("pressure", 0)
        status = "High Pressure" if pressure > 1020 else ("Low Pressure" if pressure < 1010 else "Normal")
        self.tile_pressure["val"].config(text=f"{pressure} hPa")
        if self.tile_pressure["sub"]:
            self.tile_pressure["sub"].config(text=f"Atmospheric condition: {status}")

        # 4. Visibility Tile
        raw_vis = current_data.get("visibility")
        if raw_vis is not None:
            vis_val = raw_vis / 1000 if self.units == "metric" else raw_vis / 1609.34
            vis_text = f"{vis_val:.1f} {dist_unit}"
            vis_sub = "Excellent visual clarity" if vis_val >= 10 else "Reduced sight distance"
        else:
            vis_text = "N/A"
            vis_sub = "--"
        self.tile_visibility["val"].config(text=vis_text)
        if self.tile_visibility["sub"]:
            self.tile_visibility["sub"].config(text=vis_sub)

        # 5. Cloud Cover Tile
        clouds = current_data.get("clouds", {}).get("all", 0)
        self.tile_clouds["val"].config(text=f"{clouds}%")
        self._draw_progress_bar(self.tile_clouds["bar"], clouds, 100, ACCENT_AMBER if clouds < 30 else ACCENT_SKY)
        if self.tile_clouds["sub"]:
            cloud_desc = "Clear sky" if clouds < 20 else ("Partly cloudy" if clouds < 60 else "Overcast skies")
            self.tile_clouds["sub"].config(text=cloud_desc)

        # 6. Sun Schedule Tile
        sys_info = current_data.get("sys", {})
        sr_ts = sys_info.get("sunrise")
        ss_ts = sys_info.get("sunset")
        sr_str = datetime.fromtimestamp(sr_ts, tz=city_tz).strftime("%I:%M %p") if sr_ts else "--"
        ss_str = datetime.fromtimestamp(ss_ts, tz=city_tz).strftime("%I:%M %p") if ss_ts else "--"
        self.tile_sun["val"].config(text=f"Rise: {sr_str}  •  Set: {ss_str}")

        if sr_ts and ss_ts and self.tile_sun["sub"]:
            daylight_seconds = max(ss_ts - sr_ts, 0)
            hours = daylight_seconds // 3600
            minutes = (daylight_seconds % 3600) // 60
            self.tile_sun["sub"].config(text=f"Total daylight duration: {hours}h {minutes:02d}m")

        # Update Forecasts
        if forecast_data:
            self._update_hourly_timeline(forecast_data, city_tz, temp_unit)
            self._update_extended_forecast(forecast_data, city_tz, temp_unit)

    def _draw_progress_bar(self, canvas, value, max_val, color):
        """Render a rounded mini progress meter on canvas."""
        if not canvas:
            return
        canvas.delete("all")
        width = 160
        height = 5
        fraction = max(0.0, min(1.0, float(value) / float(max_val)))
        fill_width = int(width * fraction)

        # Background track
        canvas.create_rectangle(0, 0, width, height, fill="#1e293b", outline="")
        # Active progress
        if fill_width > 0:
            canvas.create_rectangle(0, 0, fill_width, height, fill=color, outline="")

    def _update_hourly_timeline(self, forecast_data: dict, city_tz: timezone, temp_unit: str):
        """Render the next 6 chronological hourly intervals."""
        entries = forecast_data.get("list", [])[:6]
        for i, card in enumerate(self.hourly_cards):
            if i < len(entries):
                entry = entries[i]
                dt = datetime.fromtimestamp(entry.get("dt", 0), tz=city_tz)
                time_str = "Now" if i == 0 else dt.strftime("%I:%M %p")

                t = entry.get("main", {}).get("temp", 0)
                icon_code = entry.get("weather", [{}])[0].get("icon", "")
                pop = int(max(entry.get("pop", 0), 0) * 100)
                rain_str = f"💧 {pop}%" if pop > 0 else "-"

                card["time"].config(text=time_str)
                card["temp"].config(text=f"{t:.0f}{temp_unit}")
                card["rain"].config(text=rain_str)

                # Icon
                icon_img = self._get_icon_image(icon_code, size=(42, 42))
                if icon_img:
                    card["icon"].config(image=icon_img, text="")
                    card["icon"].image = icon_img
                else:
                    card["icon"].config(image="", text=EMOJI_FALLBACK.get(icon_code, "☁️"))
            else:
                card["time"].config(text="--")
                card["temp"].config(text="--")
                card["rain"].config(text="-")

    def _update_extended_forecast(self, forecast_data: dict, city_tz: timezone, temp_unit: str):
        """Aggregate and populate the 5-day daily forecast cards."""
        daily_groups = defaultdict(list)
        for entry in forecast_data.get("list", []):
            dt = datetime.fromtimestamp(entry.get("dt", 0), tz=city_tz)
            daily_groups[dt.date()].append(entry)

        today = datetime.now(tz=city_tz).date()
        valid_days = [d for d in daily_groups.keys() if d >= today][:5]

        for i, card in enumerate(self.forecast_cards):
            if i < len(valid_days):
                day_date = valid_days[i]
                entries = daily_groups[day_date]

                day_title = "Today" if day_date == today else day_date.strftime("%a, %b %d")
                min_t = min(e.get("main", {}).get("temp_min", 0) for e in entries)
                max_t = max(e.get("main", {}).get("temp_max", 0) for e in entries)

                mid_entry = entries[len(entries) // 2]
                cond = mid_entry.get("weather", [{}])[0].get("description", "").title()
                icon_code = mid_entry.get("weather", [{}])[0].get("icon", "")

                pop = int(max((e.get("pop", 0) for e in entries), default=0) * 100)
                pop_str = f"💧 {pop}%" if pop > 0 else "💧 -"

                card["day"].config(text=day_title)
                card["temp"].config(text=f"{min_t:.0f}° / {max_t:.0f}{temp_unit}")
                card["rain"].config(text=pop_str)
                card["cond"].config(text=cond)

                icon_img = self._get_icon_image(icon_code, size=(48, 48))
                if icon_img:
                    card["icon"].config(image=icon_img, text="")
                    card["icon"].image = icon_img
                else:
                    card["icon"].config(image="", text=EMOJI_FALLBACK.get(icon_code, "⛅"))
            else:
                card["day"].config(text="--")
                card["temp"].config(text="-- / --")
                card["rain"].config(text="--")
                card["cond"].config(text="--")

    def set_status(self, message: str, is_error: bool = False):
        """Display an inline status banner."""
        self.lbl_status.config(
            text=message,
            fg=ACCENT_ROSE if is_error else ACCENT_SKY,
        )


if __name__ == "__main__":
    app = WeatherAppGUI()
    app.mainloop()
