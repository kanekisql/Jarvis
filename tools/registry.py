from tools.time import TimeTool
from tools.weather import WeatherTool
from tools.currency import CurrencyTool
from tools.code_search import CodeSearchTool


class ToolRegistry:
    """
    Registro central de herramientas de JARVIS.

    El Registry conoce las herramientas disponibles,
    pero no decide cuándo utilizarlas.

    Esa responsabilidad será del Planner.
    """

    def __init__(self):

        self._tools = {}

        # ======================================================
        # REGISTRAR TOOLS
        # ======================================================

        self.register(
            "time",
            TimeTool()
        )

        self.register(
            "weather",
            WeatherTool()
        )

        self.register(
            "currency",
            CurrencyTool()
        )

        self.register(
            "code_search",
            CodeSearchTool()
        )

    # ==========================================================
    # REGISTRAR TOOL
    # ==========================================================

    def register(
        self,
        name: str,
        tool
    ):
        """
        Registra una herramienta usando un nombre único.
        """

        if not name:
            raise ValueError(
                "El nombre de la herramienta "
                "no puede estar vacío."
            )

        self._tools[name] = tool

    # ==========================================================
    # OBTENER TOOL
    # ==========================================================

    def get(
        self,
        name: str
    ):
        """
        Devuelve una herramienta registrada.

        Retorna None si no existe.
        """

        return self._tools.get(name)

    # ==========================================================
    # COMPROBAR EXISTENCIA
    # ==========================================================

    def has(
        self,
        name: str
    ) -> bool:
        """
        Comprueba si una herramienta está registrada.
        """

        return name in self._tools

    # ==========================================================
    # LISTAR TOOLS
    # ==========================================================

    def list_tools(self):
        """
        Devuelve los nombres de todas las herramientas
        registradas.
        """

        return list(self._tools.keys())