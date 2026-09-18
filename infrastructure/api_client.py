import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

class LightweightAPIClient:
    """Cliente HTTP liviano para consumo de APIs públicas universales."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) JARVIS/2.0"
        }

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{url}?{query_string}" if "?" not in url else f"{url}&{query_string}"
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
        except Exception:
            return None
        return None

    def get_world_time_by_city(self, city_or_country: str) -> Optional[Dict[str, str]]:
        """Obtiene la hora actual de cualquier ciudad o país vía Open-Meteo Geocoding."""
        try:
            city_clean = city_or_country.strip()
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city_clean)}&count=1&language=es"
            geo_data = self.get(geo_url)
            
            if not geo_data or not geo_data.get("results"):
                return None

            result = geo_data["results"][0]
            latitude = result["latitude"]
            longitude = result["longitude"]
            location_name = f"{result['name']}, {result.get('country', '')}"

            time_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
            time_data = self.get(time_url)

            if time_data and "current_weather" in time_data:
                raw_time = time_data["current_weather"]["time"]
                time_part = raw_time.split("T")[-1]
                return {"location": location_name, "time": time_part}
        except Exception:
            pass
        return None

    def get_weather_by_city(self, city_or_country: str) -> Optional[Dict[str, str]]:
        """Obtiene el clima actual consultando Open-Meteo o wttr.in como fallback."""
        try:
            city_clean = city_or_country.strip()
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city_clean)}&count=1&language=es"
            geo_data = self.get(geo_url)
            
            if geo_data and geo_data.get("results"):
                result = geo_data["results"][0]
                latitude, longitude = result["latitude"], result["longitude"]
                location_name = f"{result['name']}, {result.get('country', '')}"

                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
                w_data = self.get(weather_url)

                if w_data and "current_weather" in w_data:
                    temp = w_data["current_weather"]["temperature"]
                    return {"location": location_name, "temp": f"{temp}°C"}

            # Fallback vía wttr.in
            fallback_url = f"https://wttr.in/{urllib.parse.quote(city_clean)}?format=j1"
            f_data = self.get(fallback_url)
            if f_data and "current_condition" in f_data:
                temp_c = f_data["current_condition"][0]["temp_C"]
                return {"location": city_clean.title(), "temp": f"{temp_c}°C"}
        except Exception:
            pass
        return None

    def get_exchange_rate(self, base_currency: str, target_currency: str = "PEN") -> Optional[float]:
        """Consulta el tipo de cambio entre cualquier par de divisas (ISO 3 letras)."""
        try:
            url = f"https://open.er-api.com/v6/latest/{base_currency.upper()}"
            data = self.get(url)
            if data and "rates" in data:
                return data["rates"].get(target_currency.upper())
        except Exception:
            pass
        return None