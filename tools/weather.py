
from infrastructure.api_client import LightweightAPIClient


class WeatherTool:
    """
    Herramienta para consultar el clima actual.

    El IntentParser se encarga de identificar la ubicación.

    Esta herramienta recibe directamente esa ubicación
    y consulta la API correspondiente.
    """

    def __init__(self, api_client=None):
        self.api_client = api_client or LightweightAPIClient()

    def execute(self, location: str = None) -> str:

        if not location:
            location = "Lima"

        location = location.strip()

        result = self.api_client.get_weather_by_city(
            location
        )

        if not result:
            return (
                f"No pude obtener el clima actual "
                f"para {location}."
            )

        response = (
            f"La temperatura actual en "
            f"{result['location']} "
            f"es de {result['temp']}."
        )

        if result.get("apparent_temp"):
            response += (
                f" Sensación térmica: "
                f"{result['apparent_temp']}."
            )

        if result.get("wind_speed"):
            response += (
                f" Viento: "
                f"{result['wind_speed']}."
            )

        return response
