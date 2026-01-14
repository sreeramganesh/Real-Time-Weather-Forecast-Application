import requests
API_KEY = "5b14a695fe04a43058faa3d93c5ad258"
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
def main():
    city = input("Enter the city name: ")
    weather_data = get_weather(city)
    if weather_data:
        temp = weather_data['main']['temp']
        desc = weather_data['weather'][0]['description'].title()
        humidity = weather_data['main']['humidity']
        wind = weather_data['wind']['speed']
        print("\n Real-Time Weather App")
        print(f" Location: {city}")
        print(f"Temperature: {temp}°C")
        print(f" Condition: {desc}")
        print(f" Humidity: {humidity}%")
        print(f" Wind Speed: {wind} m/s")
    else:
        print(" Could not fetch weather data. Please check the city name or your internet connection.")
if __name__ == "__main__":
    main()
