# Handles all OpenWeatherMap API calls
import requests


def search_cities(query: str, api_key: str, limit: int = 5) -> list[str]:
    """City suggestions from OpenWeather Geocoding API."""
    if not query or not api_key:
        return []

    try:
        url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {"q": query, "limit": limit, "appid": api_key}
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        results = []
        seen = set()
        for item in data:
            name = item.get("name", "")
            country = item.get("country", "")
            state = item.get("state", "")
            label = f"{name}, {state}, {country}" if state else f"{name}, {country}"
            if label.lower() not in seen:
                seen.add(label.lower())
                results.append(label)
        return results
    except Exception:
        return []


def get_current_weather(city: str, api_key: str) -> dict:
    """Real-time weather for a city."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    return {
        "temp_c": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "wind_speed_kmh": round(data["wind"]["speed"] * 3.6, 1),
        "description": data["weather"][0]["description"].title(),
        "city_name": data["name"],
        "country": data["sys"]["country"],
    }


def get_forecast(city: str, api_key: str) -> list:
    """5-day / 3-hour forecast for the trend chart."""
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city, "appid": api_key, "units": "metric"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return [{
            "timestamp": item["dt_txt"],
            "temp_c": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "wind_speed_kmh": round(item["wind"]["speed"] * 3.6, 1),
        } for item in data["list"]]
    except Exception:
        return []
