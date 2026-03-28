import requests
from datetime import datetime


def run(args):
    """
    Checks for rain in the next 7 days and returns the average temperature.
    Uses Open-Meteo (No API key required) and IP-API for location.
    """
    city = args.get("city")
    lat, lon = None, None

    # 1. Get Coordinates (Open-Meteo needs Lat/Lon, not City names)
    if city:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_resp = requests.get(geo_url, timeout=5).json()
        if not geo_resp.get("results"):
            raise RuntimeError(f"City not found: {city}")

        location_data = geo_resp["results"][0]
        lat, lon = location_data["latitude"], location_data["longitude"]
        city = location_data["name"]  # Formatted name
    else:
        # Auto-detect via IP
        ip_resp = requests.get("http://ip-api.com/json/", timeout=5).json()
        if ip_resp.get("status") != "success":
            raise RuntimeError("Failed to detect location")
        lat, lon = ip_resp["lat"], ip_resp["lon"]
        city = ip_resp["city"]

    # 2. Fetch Weather Data
    # We request daily rain sum and max/min temperatures
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
        "&timezone=auto"
    )

    resp = requests.get(weather_url, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError("Failed to fetch weather data")

    data = resp.json()["daily"]

    # 3. Analyze Forecast (WMO Codes 51-99 represent various types of rain/snow)
    #
    for i in range(len(data["time"])):
        code = data["weather_code"][i]

        # WMO Codes: 51-67 (Rain/Drizzle), 80-82 (Showers), 95-99 (Thunderstorm)
        if code >= 51:
            date_str = data["time"][i]
            avg_temp = (
                data["temperature_2m_max"][i] + data["temperature_2m_min"][i]
            ) / 2
            precip = data["precipitation_sum"][i]

            return (
                f"It looks like it’s going to rain in {city} \n"
                f"Expected on: {date_str}.\n"
                f"With a total precipitation: {precip}mm.\n"
                f"Also you can expect an average temperature of about {round(avg_temp, 1)}°C."
            )

    # 4. No rain found
    today_avg = (data["temperature_2m_max"][0] + data["temperature_2m_min"][0]) / 2
    return f"No rain forecast for {city} this week. Today's average temp: {round(today_avg, 1)}°C"
