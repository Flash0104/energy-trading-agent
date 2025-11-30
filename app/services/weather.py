import httpx
from datetime import datetime
from typing import Dict, Any

class WeatherClient:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    # Coordinates for Germany (Central)
    LAT = 51.1657
    LON = 10.4515

    async def get_forecast(self) -> Dict[str, Any]:
        """
        Fetch hourly weather forecast for Germany.
        """
        params = {
            "latitude": self.LAT,
            "longitude": self.LON,
            "hourly": "temperature_2m,wind_speed_10m,direct_radiation",
            "timezone": "Europe/Berlin",
            "forecast_days": 1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def get_historical_weather(self, date: datetime) -> Dict[str, Any]:
        """
        Fetch historical weather for a specific date.
        """
        date_str = date.strftime("%Y-%m-%d")
        params = {
            "latitude": self.LAT,
            "longitude": self.LON,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,wind_speed_10m,direct_radiation",
            "timezone": "Europe/Berlin"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.ARCHIVE_URL, params=params)
            response.raise_for_status()
            return response.json()
