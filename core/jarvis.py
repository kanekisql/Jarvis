class Jarvis:
    """
    Núcleo central de JARVIS.

    Coordina los diferentes componentes del asistente
    sin contener la lógica específica de cada uno.
    """

    def __init__(self, router=None, memory=None, security=None, planner=None):
        self.router = router
        self.memory = memory
        self.security = security
        self.planner = planner

    def process(self, message: str) -> str:
        """
        Procesa un mensaje del usuario y delega su ejecución
        al componente correspondiente.
        """

        if not message or not message.strip():
            return ""

        message = message.strip()

        if self.router:
            return self.router.process_message(message)

        return "Sistema JARVIS iniciado, pero el router aún no está conectado."