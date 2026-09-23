class ToolExecutor:
    """
    Ejecutor central de herramientas de JARVIS.

    Su responsabilidad es recibir un plan,
    buscar la herramienta correspondiente en el Registry
    y ejecutarla con los argumentos proporcionados.

    El Executor NO decide qué herramienta utilizar.
    El Planner ya tomó esa decisión.
    """

    def __init__(self, tool_registry):
        self.tool_registry = tool_registry

    # ==========================================================
    # EJECUTAR PLAN
    # ==========================================================

    def execute(self, plan: dict):
        """
        Ejecuta una acción previamente preparada por el Planner.
        """

        if not plan:
            return {
                "success": False,
                "result": None,
                "error": "No se recibió ningún plan."
            }

        action = plan.get("action")

        if not action or action == "none":
            return {
                "success": False,
                "result": None,
                "error": plan.get(
                    "error",
                    "No hay ninguna acción ejecutable."
                )
            }

        # ======================================================
        # BUSCAR TOOL
        # ======================================================

        tool = self.tool_registry.get(action)

        if tool is None:
            return {
                "success": False,
                "result": None,
                "error": f"No existe la herramienta '{action}'."
            }

        # ======================================================
        # OBTENER ARGUMENTOS
        # ======================================================

        arguments = plan.get("arguments", {})

        if not isinstance(arguments, dict):
            return {
                "success": False,
                "result": None,
                "error": "Los argumentos de la herramienta no son válidos."
            }

        # ======================================================
        # EJECUTAR
        # ======================================================

        try:

            if hasattr(tool, "execute"):
                result = tool.execute(**arguments)

            elif hasattr(tool, "search_code"):
                result = tool.search_code(
                    arguments.get("query", "")
                )

            else:
                return {
                    "success": False,
                    "result": None,
                    "error": (
                        f"La herramienta '{action}' "
                        "no tiene un método ejecutable compatible."
                    )
                }

            return {
                "success": True,
                "result": result,
                "error": None
            }

        except Exception as e:

            return {
                "success": False,
                "result": None,
                "error": f"Error ejecutando '{action}': {str(e)}"
            }