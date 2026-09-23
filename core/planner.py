class Planner:
    """
    Planner central de JARVIS.

    Su responsabilidad es transformar la intención
    detectada por IntentParser en una acción estructurada.

    El Planner NO ejecuta herramientas.
    El Planner NO llama a Ollama.
    El Planner NO decide respuestas al usuario.
    """

    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry

    # ==========================================================
    # CREAR PLAN
    # ==========================================================

    def plan(self, intent_data: dict) -> dict:
        """
        Recibe los datos producidos por IntentParser
        y devuelve una acción estructurada.
        """

        if not intent_data:
            return {
                "action": "none",
                "arguments": {}
            }

        intent = intent_data.get("intent", "general")

        # ======================================================
        # GENERAL
        # ======================================================

        if intent == "general":
            return {
                "action": "general",
                "arguments": {
                    "text": intent_data.get("raw_text", "")
                }
            }

        # ======================================================
        # COMPROBAR TOOL
        # ======================================================

        if self.tool_registry is not None:

            if not self.tool_registry.has(intent):
                return {
                    "action": "none",
                    "arguments": {},
                    "error": f"No existe una herramienta registrada para '{intent}'."
                }

        # ======================================================
        # TIEMPO
        # ======================================================

        if intent == "time":
            return {
                "action": "time",
                "arguments": {
                    "location": intent_data.get("location")
                }
            }

        # ======================================================
        # CLIMA
        # ======================================================

        if intent == "weather":
            return {
                "action": "weather",
                "arguments": {
                    "location": intent_data.get("location")
                }
            }

        # ======================================================
        # MONEDA
        # ======================================================

        if intent == "currency":
            return {
                "action": "currency",
                "arguments": {
                    "amount": intent_data.get("amount"),
                    "from_currency": intent_data.get("from_currency"),
                    "to_currency": intent_data.get("to_currency")
                }
            }

        # ======================================================
        # BÚSQUEDA DE CÓDIGO
        # ======================================================

        if intent == "code_search":
            return {
                "action": "code_search",
                "arguments": {
                    "query": intent_data.get("query")
                }
            }

        # ======================================================
        # INTENCIÓN NO SOPORTADA
        # ======================================================

        return {
            "action": "none",
            "arguments": {},
            "error": f"Intención no soportada: '{intent}'."
        }