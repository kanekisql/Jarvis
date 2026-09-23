
import re
import traceback
import random

from core.intent_parser import IntentParser
from core.planner import Planner
from core.executor import ToolExecutor

from infrastructure.llm_client import OllamaClient
from infrastructure.api_client import LightweightAPIClient

from memory.manager import MemoryManager

from tools.registry import ToolRegistry
from tools.time import TimeTool
from tools.weather import WeatherTool
from tools.currency import CurrencyTool


class JarvisRouter:
    """
    Router principal de JARVIS.

    Distribuye cada consulta hacia la herramienta correspondiente:

    - Hora
    - Clima
    - Monedas
    - Búsqueda de código
    - Secretos / credenciales
    - Conversación general mediante LLM
    """

    def __init__(self):

        # =====================================================
        # COMPONENTES PRINCIPALES
        # =====================================================

        self.llm = OllamaClient()

        self.memory_manager = MemoryManager()

        self.intent_parser = IntentParser()

        # Cliente HTTP compartido
        api_client = LightweightAPIClient()

        # =====================================================
        # TOOLS
        # =====================================================

        self.time_tool = TimeTool(api_client)
        self.weather_tool = WeatherTool(api_client)
        self.currency_tool = CurrencyTool(api_client)

        # =====================================================
        # PLANNER + REGISTRY + EXECUTOR
        # =====================================================

        self.tool_registry = ToolRegistry()
        self.planner = Planner(self.tool_registry)
        self.executor = ToolExecutor(self.tool_registry)

        # =====================================================
        # HISTORIAL
        # =====================================================

        self.chat_history = ""

        # =====================================================
        # AUTENTICACIÓN
        # =====================================================

        self.authenticated = False
        self.awaiting_verification = False

        # =====================================================
        # ESTADO DE SECRETOS
        # =====================================================

        self.pending_action = None
        self.pending_service = None
        self.pending_value = None

        self.awaiting_update_confirm = False

    # ==========================================================
    # LLM
    # ==========================================================

    def _get_llm_response(
        self,
        user_input: str,
        prompt: str
    ) -> str:
        """
        Obtiene una respuesta completa desde Ollama.
        """

        try:

            try:
                stream_generator = self.llm.generate_stream(prompt)

            except TypeError:
                stream_generator = self.llm.generate_stream(
                    user_input,
                    prompt
                )

            full_response = ""

            for chunk in stream_generator:
                if chunk:
                    full_response += str(chunk)

            cleaned_response = full_response.strip()

            if cleaned_response:
                return cleaned_response

            return "No se obtuvo respuesta del modelo local."

        except Exception as e:

            print(f"\n[ERROR LLM]: {e}")
            traceback.print_exc()

            return (
                "No pude procesar la consulta "
                "en este momento."
            )

    # ==========================================================
    # SALUDO INICIAL
    # ==========================================================

    def greet_user(self) -> str:

        nombre = self.memory_manager.profile.get(
            "nombre_usuario",
            "Estheban"
        )

        return (
            f"Sistemas listos, {nombre}. "
            "¿En qué te puedo ayudar hoy?"
        )

    # ==========================================================
    # SALUDOS
    # ==========================================================

    def _handle_greeting(
        self,
        input_lower: str
    ) -> str:

        greetings = {

            "hola": [
                "Hola, Creador. ¿Qué necesitas?",
                "Hola. Te escucho, ¿qué hacemos?",
                "Hola, Creador. ¿En qué te ayudo?"
            ],

            "hola jarvis": [
                "Aquí estoy. ¿Qué necesitas?",
                "Te escucho, Creador. ¿Qué hacemos?",
                "Aquí estoy. Dime qué necesitas."
            ],

            "buenas": [
                "Buenas, Creador. ¿Qué necesitas?",
                "Buenas. Te escucho.",
                "Buenas, Creador. ¿En qué te ayudo?"
            ],

            "buenos dias": [
                "Buenos días, Creador. ¿Qué necesitas?",
                "Buenos días. Te escucho.",
                "Buenos días, Creador. ¿En qué te ayudo?"
            ],

            "buenos días": [
                "Buenos días, Creador. ¿Qué necesitas?",
                "Buenos días. Te escucho.",
                "Buenos días, Creador. ¿En qué te ayudo?"
            ],

            "buenas tardes": [
                "Buenas tardes, Creador. ¿Qué necesitas?",
                "Buenas tardes. Te escucho.",
                "Buenas tardes, Creador. ¿En qué te ayudo?"
            ],

            "buenas noches": [
                "Buenas noches, Creador. ¿Qué necesitas?",
                "Buenas noches. Te escucho.",
                "Buenas noches, Creador. ¿En qué te ayudo?"
            ],

            "despierta": [
                "Aquí estoy, Creador.",
                "Sistemas activos. Te escucho.",
                "Despierto y operativo. ¿Qué necesitas?"
            ]
        }

        return random.choice(
            greetings.get(
                input_lower,
                ["Te escucho, Creador. ¿Qué necesitas?"]
            )
        )

    # ==========================================================
    # DETECCIÓN DE SERVICIOS / SECRETOS
    # ==========================================================

    def _extract_service_and_value(
        self,
        text: str
    ):

        text_clean = re.sub(
            r"^(tú|tu):\s*",
            "",
            text,
            flags=re.IGNORECASE
        ).strip()

        services = [
            "github",
            "git hub",
            "fortnite",
            "betano",
            "gmail",
            "facebook",
            "instagram",
            "paypal",
            "ebay",
            "spotify"
        ]

        found_service = None

        for service in services:

            if service in text_clean.lower():

                if "git" in service:
                    found_service = "github"
                else:
                    found_service = service

                break

        if not found_service:

            match_service = re.search(
                r"(?:de|para)\s+([a-zA-Z0-9_-]+)",
                text_clean,
                re.IGNORECASE
            )

            if match_service:

                candidate = match_service.group(1).lower()

                if candidate not in [
                    "mi",
                    "la",
                    "una",
                    "tu",
                    "clave",
                    "contraseña"
                ]:
                    found_service = candidate

        words = text_clean.split()

        possible_value = None

        if len(words) > 1:

            last_word = words[-1]

            if last_word.lower() not in [
                "fortnite",
                "github",
                "clave",
                "contraseña",
                "password",
                "secreto",
                "para",
                "de"
            ]:

                possible_value = last_word

        return found_service, possible_value

    # ==========================================================
    # BÚSQUEDA DE CÓDIGO
    # ==========================================================

    

    # ==========================================================
    # DETECTOR DE HORA
    # ==========================================================


    # ==========================================================
    # DETECTOR DE CLIMA
    # ==========================================================


    # ==========================================================
    # DETECTOR DE MONEDAS
    # ==========================================================

    # ==========================================================
    # SALUDO PURO
    # ==========================================================

    def _is_pure_greeting(
        self,
        input_lower: str
    ) -> bool:

        cleaned = re.sub(
            r"[¿?!¡.,]+",
            " ",
            input_lower
        ).strip()

        greetings = {
            "hola",
            "hola jarvis",
            "buenas",
            "buenos dias",
            "buenos días",
            "buenas tardes",
            "buenas noches",
            "despierta"
        }

        return cleaned in greetings

    # ==========================================================
    # PROCESAR UNA INTENCIÓN
    # ==========================================================

    def _process_single_intent(
        self,
        clean_input: str
    ) -> str:

        input_lower = clean_input.lower().strip()

        # ======================================================
        # 1. PARSER CENTRAL
        # ======================================================

        datos = self.intent_parser.parse(
            clean_input
        )

        intent = datos["intent"]

        # ======================================================
        # 2. PLANNER + EXECUTOR
        # ======================================================

        if intent in [
            "time",
            "weather",
            "currency"
        ]:

            plan = self.planner.plan(
                datos
            )

            result = self.executor.execute(
                plan
            )

            if result["success"]:
                return result["result"]

            return (
                result["error"]
                or "No pude ejecutar la herramienta."
            )



        # ======================================================
        # 4. ESTADO PENDIENTE
        # ======================================================

        if (
            self.pending_service
            and not self.pending_action
            and not self.awaiting_verification
        ):

            words = clean_input.split()

            if len(words) <= 3:

                value = words[-1]

                return self._handle_secret_intent(
                    f"{self.pending_service} {value}",
                    input_lower
                )

        # ======================================================
        # 5. ALARMAS / RECORDATORIOS
        # ======================================================

        if any(
            keyword in input_lower
            for keyword in [
                "alarma",
                "despiértame",
                "despiertame",
                "recordatorio",
                "recuérdame",
                "recuerdame"
            ]
        ):

            prompt = (
                f"El usuario quiere configurar una "
                f"alarma/recordatorio: '{clean_input}'. "
                "Confirma la acción de forma directa "
                "en una sola oración."
            )

            return self._get_llm_response(
                clean_input,
                prompt
            )

        # ======================================================
        # 6. SECRETOS
        # ======================================================

        if self.memory_manager.is_secret_intent(
            clean_input
        ):

            return self._handle_secret_intent(
                clean_input,
                input_lower
            )
        # ======================================================
        # 7. BÚSQUEDA DE CÓDIGO
        # ======================================================

        if intent == "code_search":

            plan = self.planner.plan(
                datos
            )

            result = self.executor.execute(
                plan
            )

            if not result["success"]:

                return (
                    result["error"]
                    or "No pude realizar la búsqueda de código."
                )

            resultado_codigo = result["result"]

            search_target = datos.get(
                "query"
            )

            prompt = (
                f"Resume brevemente el resultado "
                f"de búsqueda de código para "
                f"'{search_target}'.\n\n"
                f"Resultado encontrado:\n"
                f"{resultado_codigo}"
            )

            return self._get_llm_response(
                clean_input,
                prompt
            )
        
        # ======================================================
        # 8. SALUDO
        # ======================================================

        if self._is_pure_greeting(
            input_lower
        ):

            return self._handle_greeting(
                input_lower
            )

        # ======================================================
        # 9. LLM GENERAL
        # ======================================================

        return self._handle_general_llm_query(
            clean_input
        )

    # ==========================================================
    # PROCESAMIENTO PRINCIPAL
    # ==========================================================

    def process_message(
        self,
        user_input: str
    ) -> str:

        clean_input = re.sub(
            r"^(tú|tu):\s*",
            "",
            user_input,
            flags=re.IGNORECASE
        ).strip()

        if not clean_input:
            return ""

        input_lower = clean_input.lower()

        # ======================================================
        # 0. CONFIRMACIÓN DE CAMBIO DE CONTRASEÑA
        # ======================================================

        if self.awaiting_update_confirm:

            self.awaiting_update_confirm = False

            if any(
                yes_keyword in input_lower
                for yes_keyword in [
                    "si",
                    "sí",
                    "actualiza",
                    "reemplaza",
                    "cambia",
                    "ok"
                ]
            ):

                self.memory_manager.save_secret(
                    self.pending_service,
                    self.pending_value
                )

                svc = self.pending_service

                self._reset_pending()

                return (
                    "Entendido. He actualizado tu "
                    f"contraseña de {svc.title()}."
                )

            svc = self.pending_service

            self._reset_pending()

            return (
                "Operación cancelada. "
                "Conservé la contraseña anterior "
                f"de {svc.title()}."
            )

        # ======================================================
        # 1. VERIFICACIÓN
        # ======================================================

        if self.awaiting_verification:

            if "eli" in input_lower:

                self.authenticated = True
                self.awaiting_verification = False

                # ==============================================
                # GUARDAR SECRETO
                # ==============================================

                if self.pending_action == "save":

                    if (
                        self.pending_service
                        and self.pending_value
                    ):

                        existing_val = (
                            self.memory_manager.get_secret(
                                self.pending_service
                            )
                        )

                        if (
                            existing_val
                            and existing_val != self.pending_value
                        ):

                            self.awaiting_update_confirm = True

                            return (
                                "Identidad confirmada. "
                                f"Ya existe una contraseña "
                                f"registrada para "
                                f"{self.pending_service.title()}. "
                                "¿Deseas reemplazarla?"
                            )

                        self.memory_manager.save_secret(
                            self.pending_service,
                            self.pending_value
                        )

                        svc = self.pending_service

                        self._reset_pending()

                        return (
                            "Identidad confirmada. "
                            f"Guardé tu contraseña de "
                            f"{svc.title()} correctamente."
                        )

                    svc = self.pending_service

                    if not svc:

                        return (
                            "Identidad confirmada. "
                            "¿De qué servicio o aplicación "
                            "deseas guardar la contraseña?"
                        )

                    return (
                        "Identidad confirmada. "
                        f"¿Cuál es la contraseña para "
                        f"{svc.title()}?"
                    )

                # ==============================================
                # CONSULTAR SECRETO
                # ==============================================

                elif self.pending_action == "query":

                    svc = self.pending_service

                    self._reset_pending()

                    if svc:

                        secret_val = (
                            self.memory_manager.get_secret(
                                svc
                            )
                        )

                        if secret_val:

                            return (
                                f"Tu contraseña de "
                                f"{svc.title()} es "
                                f"{secret_val}."
                            )

                        return (
                            "Identidad confirmada, pero "
                            f"no encontré ninguna contraseña "
                            f"para {svc.title()}."
                        )

                    return (
                        "Identidad confirmada. "
                        "¿De qué servicio o plataforma "
                        "deseas saber la clave?"
                    )

            else:

                self.awaiting_verification = False
                self._reset_pending()

                return (
                    "Verificación fallida. "
                    "Acceso denegado a los datos confidenciales."
                )

        # ======================================================
        # 2. MÚLTIPLES CONSULTAS
        # ======================================================

        sub_queries = re.split(
            r"[;\n]|(?:\s+y\s+además\s+)",
            clean_input,
            flags=re.IGNORECASE
        )

        if len(sub_queries) > 1:

            responses = []

            for sub_query in sub_queries:

                sub_query = sub_query.strip()

                if len(sub_query) > 3:

                    responses.append(
                        self._process_single_intent(
                            sub_query
                        )
                    )

            return " | ".join(responses)

        # ======================================================
        # 3. CONSULTA NORMAL
        # ======================================================

        return self._process_single_intent(
            clean_input
        )

    # ==========================================================
    # SECRETOS
    # ==========================================================

    def _handle_secret_intent(
        self,
        clean_input: str,
        input_lower: str
    ) -> str:

        service, value = (
            self._extract_service_and_value(
                clean_input
            )
        )

        is_query = any(
            query_keyword in input_lower
            for query_keyword in [
                "¿",
                "?",
                "cual",
                "cuál",
                "sabes",
                "dime",
                "muéstrame",
                "muestrame",
                "recuerdas",
                "dame"
            ]
        )

        # ======================================================
        # INFERIR VALOR PENDIENTE
        # ======================================================

        if (
            not is_query
            and not value
            and self.pending_service
            and not self.pending_action
        ):

            words = clean_input.split()

            if len(words) <= 3:

                value = words[-1]
                service = self.pending_service

        # ======================================================
        # GUARDAR
        # ======================================================

        if not is_query:

            if not value:

                self.pending_service = service

                return (
                    "¿Cuál es la contraseña que deseas "
                    "guardar para "
                    f"{service.title() if service else 'este servicio'}?"
                )

            if not self.authenticated:

                self.awaiting_verification = True
                self.pending_action = "save"
                self.pending_service = service
                self.pending_value = value

                return (
                    "Para datos confidenciales necesito "
                    "verificar tu identidad. "
                    "¿Cuál es tu juego favorito?"
                )

            existing_val = (
                self.memory_manager.get_secret(
                    service
                )
            )

            if (
                existing_val
                and existing_val != value
            ):

                self.awaiting_update_confirm = True
                self.pending_service = service
                self.pending_value = value

                return (
                    f"Ya tienes registrada una contraseña "
                    f"para {service.title()}. "
                    "¿Deseas reemplazarla?"
                )

            self.memory_manager.save_secret(
                service,
                value
            )

            return (
                f"Contraseña de {service.title()} "
                "guardada con éxito."
            )

        # ======================================================
        # CONSULTAR
        # ======================================================

        if not service:

            return (
                "¿De qué servicio o plataforma deseas "
                "consultar la contraseña?"
            )

        if not self.authenticated:

            self.awaiting_verification = True
            self.pending_action = "query"
            self.pending_service = service

            return (
                "Para datos confidenciales necesito "
                "verificar tu identidad. "
                "¿Cuál es tu juego favorito?"
            )

        secret_val = (
            self.memory_manager.get_secret(
                service
            )
        )

        if secret_val:

            return (
                f"Tu contraseña de "
                f"{service.title()} es "
                f"{secret_val}."
            )

        return (
            f"No tengo registrada ninguna contraseña "
            f"para {service.title()}."
        )

    # ==========================================================
    # LLM GENERAL
    # ==========================================================

    def _handle_general_llm_query(
        self,
        clean_input: str
    ) -> str:

        sys_context = (
            self.memory_manager.get_system_context(
                clean_input
            )
        )

        prompt = (
            f"{sys_context}\n\n"
            "REGLA: Responde en 1 o máximo 2 "
            "oraciones directas sin saludos ni relleno.\n"
            f"Pregunta: {clean_input}\n"
            "Respuesta:"
        )

        response = self._get_llm_response(
            clean_input,
            prompt
        )

        # ======================================================
        # HISTORIAL LIMITADO
        # ======================================================

        self.chat_history += (
            f"Usuario: {clean_input}\n"
            f"JARVIS: {response}\n"
        )

        lines = self.chat_history.split("\n")

        if len(lines) > 6:

            self.chat_history = "\n".join(
                lines[-6:]
            )

        return response

    # ==========================================================
    # RESET
    # ==========================================================

    def _reset_pending(self):

        self.pending_action = None
        self.pending_service = None
        self.pending_value = None
        self.awaiting_update_confirm = False

    # ==========================================================
    # CIERRE
    # ==========================================================

    def close(self):

        if hasattr(
            self.memory_manager,
            "close"
        ):

            self.memory_manager.close()

