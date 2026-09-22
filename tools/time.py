
from datetime import datetime
from zoneinfo import ZoneInfo

from infrastructure.api_client import LightweightAPIClient


class TimeTool:
    """
    Herramienta para obtener la hora local exacta
    de una ubicación.

    El IntentParser se encarga de identificar
    la ubicación.

    Esta herramienta únicamente:

        ubicación
            ↓
        geocodificación
            ↓
        zona horaria
            ↓
        hora local exacta
    """

    def __init__(self, api_client=None):
        self.api_client = api_client or LightweightAPIClient()

    def execute(self, location: str = None) -> str:

        if not location:
            location = "Lima"

        location = location.strip()

        geo = self.api_client.geocode_city(
            location
        )

        if not geo:
            return (
                f"No pude identificar la ubicación "
                f"'{location}'."
            )

        timezone_name = geo.get("timezone")

        if not timezone_name:
            return (
                f"No pude determinar la zona horaria "
                f"de {location}."
            )

        try:
            local_time = datetime.now(
                ZoneInfo(timezone_name)
            )

        except Exception:
            return (
                f"No pude obtener la hora actual "
                f"de {location}."
            )

        time_text = local_time.strftime(
            "%H:%M:%S"
        )

        display_location = geo.get(
            "name",
            location
        )

        country = geo.get("country")

        if country:
            display_location = (
                f"{display_location}, {country}"
            )

        return (
            f"La hora actual en "
            f"{display_location} "
            f"es {time_text}."
        )

