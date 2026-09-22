import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional


class LightweightAPIClient:
    """
    Cliente HTTP liviano para consumir APIs públicas.

    Diseñado para que las herramientas de JARVIS
    puedan consultar información real sin depender del LLM.
    """

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

        self.headers = {
            "User-Agent": "JARVIS/2.0",
            "Accept": "application/json",
        }

    # =========================================================
    # HTTP GENERAL
    # =========================================================

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza una petición GET y devuelve JSON.

        Retorna None si ocurre un error de conexión,
        HTTP o procesamiento de datos.
        """

        try:
            # Agregar parámetros correctamente
            if params:
                query_string = urllib.parse.urlencode(params)
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}{query_string}"

            # Combinar headers generales con headers específicos
            request_headers = self.headers.copy()

            if headers:
                request_headers.update(headers)

            request = urllib.request.Request(
                url,
                headers=request_headers,
                method="GET",
            )

            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:

                status = response.status
                content = response.read().decode("utf-8")

                if 200 <= status < 300:
                    return json.loads(content)

        except urllib.error.HTTPError:
            return None

        except urllib.error.URLError:
            return None

        except TimeoutError:
            return None

        except json.JSONDecodeError:
            return None

        except Exception:
            return None

        return None


    # =========================================================
    # GEOCODING - OPEN METEO
    # =========================================================
   
    def geocode_city(
        self,
        city_or_country: str
    ) -> Optional[Dict[str, Any]]:
        """
        Resuelve una ciudad o país mediante Open-Meteo.

        Primero normaliza algunos nombres geográficos
        ambiguos y luego consulta Open-Meteo.
        """

        query = city_or_country.strip()

        if not query:
            return None

        # ======================================================
        # Normalización de nombres geográficos ambiguos
        # ======================================================

        aliases = {
            "new york": "New York City",
            "nueva york": "New York City",
            "mexico": "Mexico City",
            "méxico": "Mexico City",
            "ciudad de mexico": "Mexico City",
            "ciudad de méxico": "Mexico City",
        }

        query_normalized = query.lower().strip()

        query = aliases.get(
            query_normalized,
            query
        )

        # ======================================================
        # Consulta a Open-Meteo
        # ======================================================

        params = {
            "name": query,
            "count": 10,
            "language": "es",
            "format": "json",
        }

        data = self.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params=params,
        )

        if not data or not data.get("results"):
            return None

        results = data["results"]

        query_normalized = query.lower().strip()

        # ======================================================
        # Coincidencia exacta
        # ======================================================

        exact_matches = [
            result
            for result in results
            if str(
                result.get("name", "")
            ).lower().strip()
            == query_normalized
        ]

        if exact_matches:
            result = exact_matches[0]

        else:
            # ==================================================
            # Si no hay coincidencia exacta,
            # elegir la ubicación con mayor población
            # ==================================================

            result = max(
                results,
                key=lambda item: (
                    item.get("population") or 0
                )
            )

        # ======================================================
        # Resultado estructurado
        # ======================================================

        return {
            "name": result.get("name"),
            "country": result.get("country"),
            "country_code": result.get("country_code"),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "timezone": result.get("timezone"),
            "admin1": result.get("admin1"),
            "population": result.get("population"),
            "feature_code": result.get("feature_code"),
        }


    # =========================================================
    # HORA
    # =========================================================

    def get_world_time_by_city(
        self,
        city_or_country: str
    ) -> Optional[Dict[str, str]]:
        """
        Obtiene la hora local exacta de una ciudad
        respetando su zona horaria.
        """

        location = self.geocode_city(city_or_country)

        if not location:
            return None

        params = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "time",
            "timezone": "auto",
        }

        data = self.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
        )

        if not data or "current" not in data:
            return None

        raw_time = data["current"].get("time")

        if not raw_time:
            return None

        # Open-Meteo devuelve:
        # 2026-09-21T12:12
        #
        # Conservamos exactamente:
        # 12:12
        time_part = raw_time.split("T", 1)[-1]

        location_name = location["name"]

        if location.get("admin1"):
            location_name += f", {location['admin1']}"

        if location.get("country"):
            location_name += f", {location['country']}"

        return {
            "location": location_name,
            "time": time_part,
            "timezone": data.get("timezone", ""),
        }
    # =========================================================
    # CLIMA
    # =========================================================

    def get_weather_by_city(
        self,
        city_or_country: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene las condiciones meteorológicas actuales
        de una ubicación mediante Open-Meteo.
        """

        location = self.geocode_city(city_or_country)

        if not location:
            return None

        params = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": (
                "temperature_2m,"
                "apparent_temperature,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "auto",
        }

        data = self.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
        )

        if not data or "current" not in data:
            return None

        current = data["current"]

        temperature = current.get("temperature_2m")
        apparent = current.get("apparent_temperature")
        weather_code = current.get("weather_code")
        wind_speed = current.get("wind_speed_10m")

        if temperature is None:
            return None

        location_name = location["name"]

        if location.get("admin1"):
            location_name += f", {location['admin1']}"

        if location.get("country"):
            location_name += f", {location['country']}"

        return {
            "location": location_name,
            "temp": f"{temperature}°C",
            "apparent_temp": (
                f"{apparent}°C"
                if apparent is not None
                else None
            ),
            "weather_code": weather_code,
            "wind_speed": (
                f"{wind_speed} km/h"
                if wind_speed is not None
                else None
            ),
            "timezone": data.get("timezone", ""),
            "time": current.get("time"),
        }

    # =========================================================
    # MONEDAS
    # =========================================================

    def get_exchange_rate(
        self,
        base_currency: str,
        target_currency: str = "PEN"
    ) -> Optional[float]:
        """
        Obtiene el tipo de cambio de referencia entre
        dos monedas utilizando ExchangeRate API.
        """

        base = base_currency.upper().strip()
        target = target_currency.upper().strip()

        if len(base) != 3 or len(target) != 3:
            return None

        url = f"https://open.er-api.com/v6/latest/{base}"

        data = self.get(url)

        if not data:
            return None

        rates = data.get("rates")

        if not rates:
            return None

        rate = rates.get(target)

        if rate is None:
            return None

        try:
            return float(rate)
        except (TypeError, ValueError):
            return None