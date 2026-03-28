import requests


def run(args):
    city = args.get("city")
    lat, lon, city_name = None, None, None

    # Resolve coordinates
    if city:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=5,
        ).json()
        if not geo.get("results"):
            return f"City not found: {city}"
        r = geo["results"][0]
        lat, lon, city_name = r["latitude"], r["longitude"], r["name"]
    else:
        ip = requests.get("http://ip-api.com/json/", timeout=5).json()
        if ip.get("status") != "success":
            return "Could not detect your location."
        lat, lon, city_name = ip["lat"], ip["lon"], ip["city"]

    # Fetch forecast
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            },
            timeout=5,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return "Failed to fetch weather data."

    daily = resp.json()["daily"]

    # Find first rainy day (WMO codes >= 51 = precipitation)
    for i, code in enumerate(daily["weather_code"]):
        if code >= 51:
            avg_temp = (daily["temperature_2m_max"][i] + daily["temperature_2m_min"][i]) / 2
            return (
                f"Rain expected in {city_name} on {daily['time'][i]}, "
                f"with {daily['precipitation_sum'][i]}mm of precipitation "
                f"and an average temperature of {round(avg_temp, 1)}°C."
            )

    today_avg = (daily["temperature_2m_max"][0] + daily["temperature_2m_min"][0]) / 2
    return f"No rain forecast for {city_name} this week. Today's average: {round(today_avg, 1)}°C."