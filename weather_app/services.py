import requests
from datetime import datetime

# WMO Weather Codes mapping to human-readable text and emojis
WMO_CODES = {
    0: {"desc": "Clear sky", "emoji": "☀️"},
    1: {"desc": "Mainly clear", "emoji": "🌤️"},
    2: {"desc": "Partly cloudy", "emoji": "⛅"},
    3: {"desc": "Overcast", "emoji": "☁️"},
    45: {"desc": "Foggy", "emoji": "🌫️"},
    48: {"desc": "Depositing rime fog", "emoji": "🌫️"},
    51: {"desc": "Light drizzle", "emoji": "🌧️"},
    53: {"desc": "Moderate drizzle", "emoji": "🌧️"},
    55: {"desc": "Dense drizzle", "emoji": "🌧️"},
    56: {"desc": "Light freezing drizzle", "emoji": "❄️"},
    57: {"desc": "Dense freezing drizzle", "emoji": "❄️"},
    61: {"desc": "Slight rain", "emoji": "🌧️"},
    63: {"desc": "Moderate rain", "emoji": "🌧️"},
    65: {"desc": "Heavy rain", "emoji": "🌧️"},
    66: {"desc": "Light freezing rain", "emoji": "❄️"},
    67: {"desc": "Heavy freezing rain", "emoji": "❄️"},
    71: {"desc": "Slight snowfall", "emoji": "❄️"},
    73: {"desc": "Moderate snowfall", "emoji": "❄️"},
    75: {"desc": "Heavy snowfall", "emoji": "❄️"},
    77: {"desc": "Snow grains", "emoji": "❄️"},
    80: {"desc": "Slight rain showers", "emoji": "🌧️"},
    81: {"desc": "Moderate rain showers", "emoji": "🌧️"},
    82: {"desc": "Violent rain showers", "emoji": "⛈️"},
    85: {"desc": "Slight snow showers", "emoji": "❄️"},
    86: {"desc": "Heavy snow showers", "emoji": "❄️"},
    95: {"desc": "Thunderstorm", "emoji": "⛈️"},
    96: {"desc": "Thunderstorm with slight hail", "emoji": "⛈️"},
    99: {"desc": "Thunderstorm with heavy hail", "emoji": "⛈️"},
}

def get_weather_desc(code):
    return WMO_CODES.get(code, {"desc": "Unknown weather condition", "emoji": "🌡️"})

class WeatherService:
    @staticmethod
    def geocode_city(city_name):
        """
        Geocodes a city name to latitude and longitude.
        Returns a dict with lat, lon, city name, country name, or None if not found.
        """
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": city_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results")
            if not results:
                return None
            
            result = results[0]
            return {
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "city": result.get("name"),
                "country": result.get("country", "")
            }
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    @classmethod
    def get_weather_data(cls, lat, lon):
        """
        Fetches the current weather and 5-day forecast for the given latitude and longitude.
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,pressure_msl,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
            "timezone": "auto"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current_raw = data.get("current", {})
            daily_raw = data.get("daily", {})
            
            # Parse current weather description and emoji
            current_weather_info = get_weather_desc(current_raw.get("weather_code", 0))
            
            # Format sunrise and sunset times
            sunrise_str = daily_raw.get("sunrise", [""])[0]
            sunset_str = daily_raw.get("sunset", [""])[0]
            
            def format_iso_time(iso_str):
                try:
                    dt = datetime.fromisoformat(iso_str)
                    return dt.strftime("%I:%M %p")
                except ValueError:
                    return "N/A"

            # Prepare 5-day forecast
            forecast = []
            dates = daily_raw.get("time", [])
            codes = daily_raw.get("weather_code", [])
            max_temps = daily_raw.get("temperature_2m_max", [])
            min_temps = daily_raw.get("temperature_2m_min", [])
            
            for i in range(min(5, len(dates))):
                try:
                    dt = datetime.strptime(dates[i], "%Y-%m-%d")
                    day_name = dt.strftime("%A")
                    date_formatted = dt.strftime("%b %d")
                except ValueError:
                    day_name = dates[i]
                    date_formatted = ""
                    
                w_info = get_weather_desc(codes[i] if i < len(codes) else 0)
                forecast.append({
                    "day": day_name,
                    "date": date_formatted,
                    "max_temp": max_temps[i] if i < len(max_temps) else "N/A",
                    "min_temp": min_temps[i] if i < len(min_temps) else "N/A",
                    "desc": w_info["desc"],
                    "emoji": w_info["emoji"]
                })

            return {
                "current": {
                    "temp": current_raw.get("temperature_2m"),
                    "feels_like": current_raw.get("apparent_temperature"),
                    "humidity": current_raw.get("relative_humidity_2m"),
                    "wind_speed": current_raw.get("wind_speed_10m"),
                    "pressure": current_raw.get("pressure_msl"),
                    "desc": current_weather_info["desc"],
                    "emoji": current_weather_info["emoji"],
                    "sunrise": format_iso_time(sunrise_str),
                    "sunset": format_iso_time(sunset_str)
                },
                "forecast": forecast
            }
        except Exception as e:
            print(f"Weather data error: {e}")
            return None
