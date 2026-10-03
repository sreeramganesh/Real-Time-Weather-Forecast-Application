import os
import sys
from datetime import datetime, timezone, timedelta
import requests
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables from .env file if present
load_dotenv()

# Load API key securely from environment variable or .env file
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_weather(city: str) -> dict | None:
    """Fetch real-time weather data for a given city from OpenWeatherMap API."""
    if not API_KEY:
        print(Fore.LIGHTRED_EX + "[!] Error: OpenWeatherMap API key is missing.")
        print(Fore.YELLOW + "[!] Add OPENWEATHER_API_KEY to your .env file or set it as an environment variable.")
        return None

    params = {
        "q": city.strip(),
        "appid": API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200:
            return data
        elif response.status_code == 404:
            print(Fore.LIGHTRED_EX + f"[!] Error: City '{city}' not found. Please verify the spelling.")
        elif response.status_code == 401:
            print(Fore.LIGHTRED_EX + "[!] Error: Invalid API key. Please check your credentials.")
        elif response.status_code == 429:
            print(Fore.YELLOW + "[!] Error: Rate limit exceeded. Please try again shortly.")
        else:
            message = data.get("message", "Failed to retrieve weather data.")
            print(Fore.LIGHTRED_EX + f"[!] Error ({response.status_code}): {message.capitalize()}")

    except requests.Timeout:
        print(Fore.LIGHTRED_EX + "[!] Network error: The request timed out. Please try again.")
    except requests.ConnectionError:
        print(Fore.LIGHTRED_EX + "[!] Connection error: Unable to connect. Please check your internet connection.")
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + f"[!] Network error: {e}")

    return None


def get_forecast(city: str) -> dict | None:
    """Fetch 5-day / 3-hour forecast data for a given city from OpenWeatherMap API."""
    params = {
        "q": city.strip(),
        "appid": API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass

    return None


def get_temp_color(temp) -> str:
    """Return appropriate Colorama color depending on temperature value."""
    try:
        temp_val = float(temp)
        if temp_val >= 30:
            return Fore.LIGHTRED_EX    # Hot
        elif temp_val >= 20:
            return Fore.LIGHTYELLOW_EX # Warm
        elif temp_val >= 10:
            return Fore.LIGHTGREEN_EX  # Mild
        else:
            return Fore.LIGHTCYAN_EX   # Cool / Cold
    except (ValueError, TypeError):
        return Fore.WHITE


def display_weather(weather_data: dict, input_city: str) -> None:
    """Format and display weather details with colorized output and sunrise/sunset."""
    city_name = weather_data.get("name", input_city)
    sys_info = weather_data.get("sys", {})
    country = sys_info.get("country", "")
    location_str = f"{city_name}, {country}" if country else city_name

    main_info = weather_data.get("main", {})
    temp = main_info.get("temp", "N/A")
    feels_like = main_info.get("feels_like", "N/A")
    humidity = main_info.get("humidity", "N/A")
    pressure = main_info.get("pressure", "N/A")

    weather_list = weather_data.get("weather", [])
    desc = weather_list[0].get("description", "N/A").title() if weather_list else "N/A"
    wind_speed = weather_data.get("wind", {}).get("speed", "N/A")

    # Calculate local sunrise and sunset using city's timezone offset
    timezone_offset = weather_data.get("timezone", 0)
    city_tz = timezone(timedelta(seconds=timezone_offset))

    sunrise_ts = sys_info.get("sunrise")
    sunset_ts = sys_info.get("sunset")

    sunrise_str = (
        datetime.fromtimestamp(sunrise_ts, tz=city_tz).strftime("%I:%M %p")
        if sunrise_ts
        else "N/A"
    )
    sunset_str = (
        datetime.fromtimestamp(sunset_ts, tz=city_tz).strftime("%I:%M %p")
        if sunset_ts
        else "N/A"
    )

    temp_color = get_temp_color(temp)
    border = Fore.CYAN + "=" * 46

    print("\n" + border)
    print(Fore.CYAN + Style.BRIGHT + "            REAL-TIME WEATHER REPORT")
    print(border)
    print(f"  {Style.BRIGHT}Location:{Style.RESET_ALL}     {Fore.WHITE + Style.BRIGHT}{location_str}")
    print(f"  {Style.BRIGHT}Temperature:{Style.RESET_ALL}  {temp_color}{temp} °C {Style.DIM}(Feels like: {feels_like} °C)")
    print(f"  {Style.BRIGHT}Condition:{Style.RESET_ALL}    {Fore.MAGENTA + Style.BRIGHT}{desc}")
    print(f"  {Style.BRIGHT}Humidity:{Style.RESET_ALL}     {Fore.LIGHTBLUE_EX}{humidity}%")
    print(f"  {Style.BRIGHT}Wind Speed:{Style.RESET_ALL}   {Fore.LIGHTCYAN_EX}{wind_speed} m/s")
    print(f"  {Style.BRIGHT}Pressure:{Style.RESET_ALL}     {Fore.WHITE}{pressure} hPa")
    print(f"  {Style.BRIGHT}Sunrise:{Style.RESET_ALL}      {Fore.YELLOW}{sunrise_str} {Style.DIM}(Local Time)")
    print(f"  {Style.BRIGHT}Sunset:{Style.RESET_ALL}       {Fore.YELLOW}{sunset_str} {Style.DIM}(Local Time)")
    print(border + "\n")


def display_forecast(forecast_data: dict) -> None:
    """Format and display a 5-day weather forecast summary table."""
    city_info = forecast_data.get("city", {})
    timezone_offset = city_info.get("timezone", 0)
    city_tz = timezone(timedelta(seconds=timezone_offset))

    # Group forecast entries by calendar day in the city's local timezone
    daily_groups: dict = {}
    for entry in forecast_data.get("list", []):
        entry_dt = datetime.fromtimestamp(entry.get("dt", 0), tz=city_tz)
        day_date = entry_dt.date()
        daily_groups.setdefault(day_date, []).append(entry)

    today_date = datetime.now(tz=city_tz).date()
    border = Fore.CYAN + "-" * 62

    print(border)
    print(Fore.CYAN + Style.BRIGHT + "                   5-DAY EXTENDED FORECAST")
    print(border)
    print(
        Fore.WHITE
        + Style.BRIGHT
        + f"  {'Day':<14} {'Min / Max Temp':<19} {'Rain':<8} {'Condition'}"
    )
    print(border)

    displayed_days = 0
    for day_date, entries in daily_groups.items():
        if day_date < today_date:
            continue
        if displayed_days >= 5:
            break

        day_label = "Today" if day_date == today_date else day_date.strftime("%a, %b %d")
        min_temp = min(e.get("main", {}).get("temp_min", 0) for e in entries)
        max_temp = max(e.get("main", {}).get("temp_max", 0) for e in entries)

        # Midday entry or median entry for representative daytime weather
        mid_entry = entries[len(entries) // 2]
        weather_list = mid_entry.get("weather", [])
        condition = weather_list[0].get("description", "N/A").title() if weather_list else "N/A"

        # Precipitation probability
        max_pop = max((e.get("pop", 0) for e in entries), default=0)
        pop_percent = int(max_pop * 100)
        pop_str = f"{pop_percent}%" if pop_percent > 0 else "-"

        min_col = get_temp_color(min_temp)
        max_col = get_temp_color(max_temp)
        temp_str = f"{min_col}{min_temp:4.1f}°C{Style.RESET_ALL} / {max_col}{max_temp:4.1f}°C{Style.RESET_ALL}"
        rain_col = Fore.LIGHTBLUE_EX if pop_percent >= 40 else (Fore.CYAN if pop_percent > 0 else Fore.WHITE)

        print(
            f"  {Style.BRIGHT}{day_label:<14}{Style.RESET_ALL} "
            f"{temp_str}   "
            f"{rain_col}{pop_str:<8}{Style.RESET_ALL} "
            f"{Fore.MAGENTA}{condition}{Style.RESET_ALL}"
        )
        displayed_days += 1

    print(border + "\n")


def main():
    print(Fore.CYAN + Style.BRIGHT + "\n=== OpenWeatherMap Interactive CLI App ===")
    print(Style.DIM + "Type a city name to search, or 'q' / 'exit' to quit.\n")

    while True:
        try:
            city = input(Fore.GREEN + Style.BRIGHT + "Enter city name: " + Style.RESET_ALL).strip()
        except (KeyboardInterrupt, EOFError):
            print(Fore.CYAN + "\n\nGoodbye! Have a great day.")
            break

        if city.lower() in ("q", "quit", "exit"):
            print(Fore.CYAN + "\nThank you for using Weather App. Goodbye!\n")
            break

        if not city:
            print(Fore.YELLOW + "[!] City name cannot be empty. Please enter a city name.\n")
            continue

        weather_data = get_weather(city)
        if weather_data:
            display_weather(weather_data, city)
            forecast_data = get_forecast(city)
            if forecast_data:
                display_forecast(forecast_data)


if __name__ == "__main__":
    main()