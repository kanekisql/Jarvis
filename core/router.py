import json
import re
import traceback
from infrastructure.llm_client import OllamaClient
from memory.manager import MemoryManager
from tools.code_search import CodeSearchTool
from infrastructure.api_client import LightweightAPIClient

class JarvisRouter:
    def __init__(self):
        self.llm = OllamaClient()
        self.memory_manager = MemoryManager()
        self.code_search = CodeSearchTool()
        self.api_client = LightweightAPIClient()
        self.chat_history = ""
        
        # Estado de autenticación y flujos pendientes
        self.authenticated = False
        self.awaiting_verification = False
        self.pending_action = None        # 'save' o 'query'
        self.pending_service = None
        self.pending_value = None
        self.awaiting_update_confirm = False # Confirmación para actualizar duplicados

    def _get_llm_response(self, user_input: str, prompt: str) -> str:
        """Consume el generador por streaming de OllamaClient y retorna el texto completo."""
        try:
            try:
                stream_generator = self.llm.generate_stream(prompt)
            except TypeError:
                stream_generator = self.llm.generate_stream(user_input, prompt)
            
            full_response = ""
            for chunk in stream_generator:
                if chunk:
                    full_response += str(chunk)
            
            cleaned_response = full_response.strip()
            return cleaned_response if cleaned_response else "No se obtuvo respuesta del modelo local."

        except Exception as e:
            print(f"\n[ERROR LLM]: {e}")
            traceback.print_exc()
            return "No pude procesar la consulta en este momento."

    def _extract_intent_json(self, user_input: str) -> dict:
            system_prompt = (
                "Eres un extractor NLU. Responde ÚNICAMENTE en JSON de una línea sin explicaciones.\n"
                "Formatos:\n"
                "- Divisas: {\"intent\": \"currency\", \"from\": \"USD\", \"to\": \"PEN\"}\n"
                "- Hora: {\"intent\": \"time\", \"location\": \"Tokio\"}\n"
                "- Clima: {\"intent\": \"weather\", \"location\": \"Madrid\"}\n"
                "- General: {\"intent\": \"general\"}\n"
                f"Entrada: {user_input}"
            )
            
            raw_response = self._get_llm_response(user_input, system_prompt)
            try:
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except Exception:
                pass
            
            return {"intent": "general"}

    def greet_user(self) -> str:
        """Saludo inicial conciso e instantáneo."""
        nombre = self.memory_manager.profile.get('nombre_usuario', 'Estheban')
        return f"Sistemas listos, {nombre}. ¿En qué te puedo ayudar hoy?"

    def _extract_service_and_value(self, text: str):
        """Extrae el servicio (ej: Fortnite, GitHub) y el valor/clave."""
        text_clean = re.sub(r'^(tú|tu):\s*', '', text, flags=re.IGNORECASE).strip()
        
        services = ["github", "git hub", "fortnite", "betano", "gmail", "facebook", "instagram", "paypal", "ebay", "spotify"]
        found_service = None
        for s in services:
            if s in text_clean.lower():
                found_service = "github" if "git" in s else s
                break
        
        if not found_service:
            match_s = re.search(r'(?:de|para)\s+([a-zA-Z0-9_-]+)', text_clean, re.IGNORECASE)
            if match_s and match_s.group(1).lower() not in ["mi", "la", "una", "tu", "clave", "contraseña"]:
                found_service = match_s.group(1).lower()

        words = text_clean.split()
        possible_value = None
        if len(words) > 1:
            last_word = words[-1]
            if last_word.lower() not in ["fortnite", "github", "clave", "contraseña", "password", "secreto", "para", "de"]:
                possible_value = last_word

        return found_service, possible_value

    def _extract_search_term(self, text: str) -> str:
        """Extrae términos para la herramienta de búsqueda de código."""
        match = re.search(r'busca\s+(?:donde\s+esta\s+|dónde\s+está\s+|donde\s+se\s+usa\s+|dónde\s+se\s+usa\s+)?([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        clean = re.sub(r'["\'¿?¡!]', '', text).strip()
        stopwords = [r'\bbusca\b', r'\bdonde\b', r'\bdónde\b', r'\bse usa\b', r'\bclase\b', r'\bfuncion\b', r'\bcodigo\b']
        for word in stopwords:
            clean = re.sub(word, '', clean, flags=re.IGNORECASE)
        return clean.strip().split()[-1] if clean.strip() else ""

    def _process_single_intent(self, clean_input: str) -> str:
            """Procesa una única intención delegando en los métodos auxiliares correspondientes."""
            input_lower = clean_input.lower()

            # A) SALUDOS DIRECTOS E INSTANTÁNEOS (Fast-Path)
            greetings = ["hola", "hola jarvis", "buenas", "buenos dias", "buenos días", "buenas noches", "despierta"]
            if any(input_lower == g or input_lower.startswith(g) for g in greetings):
                return self.greet_user()

            # B) CONTINUACIÓN DE ESTADO: El usuario responde un valor/clave pendiente (ej. "7227")
            if self.pending_service and not self.pending_action and not self.awaiting_verification:
                words = clean_input.split()
                if len(words) <= 3:
                    value = words[-1]
                    # Reutilizamos el helper de secretos pasandole el servicio pendiente + el valor
                    return self._handle_secret_intent(f"{self.pending_service} {value}", input_lower)

            # C) Manejo de Alarmas y Recordatorios
            if any(kw in input_lower for kw in ["alarma", "despiértame", "despiertame", "recordatorio", "recuérdame", "recuerdame"]):
                prompt = (
                    f"El usuario quiere configurar una alarma/recordatorio: '{clean_input}'. "
                    f"Confirma la acción de forma ultra directa en 1 oración."
                )
                return self._get_llm_response(clean_input, prompt)

            # D) Manejo Inteligente de Secretos y Sinónimos (DELEGADO)
            if self.memory_manager.is_secret_intent(clean_input):
                return self._handle_secret_intent(clean_input, input_lower)

            # E) Búsqueda de Código
            code_keywords = ["busca", "donde esta", "dónde está", "se usa", "donde se usa"]
            if any(kw in input_lower for kw in code_keywords):
                search_target = self._extract_search_term(clean_input)
                if search_target and len(search_target) >= 2:
                    resultado_tgrep = self.code_search.search_code(search_target)
                    prompt = f"Resume brevemente el resultado de código encontrado para '{search_target}':\n{resultado_tgrep}"
                    return self._get_llm_response(clean_input, prompt)
                else:
                    return "Especifica qué término o función deseas que busque en tu código."

            # F) Consultas de APIs Externas Dinámicas (DELEGADO)
            api_triggers = ["hora", "tiempo", "clima", "temperatura", "cambio", "dolar", "dólar", "euro", "yen", "peso", "moneda", "convertir", "cotizacion", "cotización"]
            if any(trigger in input_lower for trigger in api_triggers):
                api_response = self._handle_api_intent(clean_input)
                if api_response is not None:
                    return api_response

            # G) Consultas Generales / Contexto (DELEGADO)
            return self._handle_general_llm_query(clean_input)
    
    def process_message(self, user_input: str) -> str:
        clean_input = re.sub(r'^(tú|tu):\s*', '', user_input, flags=re.IGNORECASE).strip()
        input_lower = clean_input.lower()

        # 0. Confirmación de actualización de contraseña
        if self.awaiting_update_confirm:
            self.awaiting_update_confirm = False
            if any(yes_kw in input_lower for yes_kw in ["si", "sí", "actualiza", "reemplaza", "cambia", "ok"]):
                self.memory_manager.save_secret(self.pending_service, self.pending_value)
                svc, val = self.pending_service, self.pending_value
                self._reset_pending()
                return f"Entendido. He actualizado tu contraseña de {svc.title()} a {val}."
            else:
                svc = self.pending_service
                self._reset_pending()
                return f"Operación cancelada. Conservé la contraseña anterior de {svc.title()}."

        # 1. Pregunta trampa de verificación
        if self.awaiting_verification:
            if "eli" in input_lower:
                self.authenticated = True
                self.awaiting_verification = False
                
                if self.pending_action == "save":
                    if self.pending_service and self.pending_value:
                        existing_val = self.memory_manager.get_secret(self.pending_service)
                        if existing_val and existing_val != self.pending_value:
                            self.awaiting_update_confirm = True
                            return (f"Identidad confirmada. Ya existe una contraseña registrada para {self.pending_service.title()} ({existing_val}). "
                                    f"¿Deseas reemplazarla por {self.pending_value}?")
                        
                        self.memory_manager.save_secret(self.pending_service, self.pending_value)
                        svc = self.pending_service
                        self._reset_pending()
                        return f"Identidad confirmada. Guardé tu contraseña de {svc.title()} correctamente."
                    else:
                        svc = self.pending_service
                        if not svc:
                            return "Identidad confirmada. ¿De qué servicio o aplicación deseas guardar la contraseña?"
                        return f"Identidad confirmada. ¿Cuál es la contraseña para {svc.title()}?"

                elif self.pending_action == "query":
                    svc = self.pending_service
                    self._reset_pending()
                    if svc:
                        secret_val = self.memory_manager.get_secret(svc)
                        if secret_val:
                            return f"Tu contraseña de {svc.title()} es {secret_val}."
                        else:
                            return f"Identidad confirmada, pero no encontré ninguna contraseña para {svc.title()}."
                    else:
                        return "Identidad confirmada. ¿De qué servicio o plataforma deseas saber la clave?"
            else:
                self.awaiting_verification = False
                self._reset_pending()
                return "Verificación fallida. Acceso denegado a los datos confidenciales."

    # Divorcio de preguntas múltiples solo cuando hay puntos, comas o conectores claros
        sub_queries = re.split(r'[\n;]|(?:\s+y\s+además\s+)', clean_input, flags=re.IGNORECASE)
        if len(sub_queries) > 1:
            responses = []
            for sub in sub_queries:
                if len(sub.strip()) > 3:
                    responses.append(self._process_single_intent(sub.strip()))
            return " | ".join(responses)
        
        return self._process_single_intent(clean_input)

    def _handle_secret_intent(self, clean_input: str, input_lower: str) -> str:
        """Gestiona la lógica de guardar y consultar credenciales/secretos."""
        service, value = self._extract_service_and_value(clean_input)
        is_query = any(q in input_lower for q in ["¿", "?", "cual", "cuál", "sabes", "dime", "muéstrame", "recuerdas", "dame"])

        # Intento de inferir valor si venía de un estado previo
        if not is_query and not value and self.pending_service and not self.pending_action:
            words = clean_input.split()
            if len(words) <= 3:
                value = words[-1]
                service = self.pending_service

        # --- FLUJO DE GUARDADO ---
        if not is_query:
            if not value:
                self.pending_service = service
                return f"¿Cuál es la contraseña que deseas guardar para {service.title() if service else 'este servicio'}?"

            if not self.authenticated:
                self.awaiting_verification = True
                self.pending_action = "save"
                self.pending_service = service
                self.pending_value = value
                return "Para datos confidenciales necesito verificar tu identidad. ¿Cuál es tu juego favorito?"

            existing_val = self.memory_manager.get_secret(service)
            if existing_val and existing_val != value:
                self.awaiting_update_confirm = True
                self.pending_service = service
                self.pending_value = value
                return f"Ya tienes registrada una contraseña para {service.title()} ({existing_val}). ¿Deseas reemplazarla por {value}?"

            self.memory_manager.save_secret(service, value)
            return f"Contraseña de {service.title()} guardada con éxito."

        # --- FLUJO DE CONSULTA ---
        if not service:
            return "¿De qué servicio o plataforma deseas consultar la contraseña?"

        if not self.authenticated:
            self.awaiting_verification = True
            self.pending_action = "query"
            self.pending_service = service
            return "Para datos confidenciales necesito verificar tu identidad. ¿Cuál es tu juego favorito?"

        secret_val = self.memory_manager.get_secret(service)
        return f"Tu contraseña de {service.title()} es {secret_val}." if secret_val else f"No tengo registrada ninguna contraseña para {service.title()}."

    def _handle_api_intent(self, clean_input: str) -> str | None:
        """Procesa intenciones NLU asignadas a servicios dinámicos externos (moneda, hora, clima)."""
        parsed_intent = self._extract_intent_json(clean_input)
        intent_type = parsed_intent.get("intent")

        if intent_type == "currency":
            from_curr = parsed_intent.get("from", "USD").upper()
            to_curr = parsed_intent.get("to", "PEN").upper()
            rate = self.api_client.get_exchange_rate(from_curr, to_curr)
            if rate:
                compra = round(rate * 0.99, 2)
                venta = round(rate * 1.01, 2)
                return f"El tipo de cambio de {from_curr} a {to_curr} es {rate:.2f} (Compra aprox: {compra:.2f} | Venta aprox: {venta:.2f})."
            return f"No pude obtener la cotización de {from_curr} a {to_curr} en este momento."

        if intent_type == "time":
            loc = parsed_intent.get("location", "Lima")
            time_res = self.api_client.get_world_time_by_city(loc)
            return f"La hora exacta en {time_res['location']} es las {time_res['time']} hrs." if time_res else f"No pude obtener la hora para {loc}."

        if intent_type == "weather":
            loc = parsed_intent.get("location", "Lima")
            weather_res = self.api_client.get_weather_by_city(loc)
            return f"La temperatura actual en {weather_res['location']} es de {weather_res['temp']}." if weather_res else f"No pude obtener el clima para {loc}."

        return None  # Si el intent_type era "general", pasa al LLM

    def _handle_general_llm_query(self, clean_input: str) -> str:
        """Maneja las consultas generales agregando contexto y gestionando la memoria de conversación."""
        sys_context = self.memory_manager.get_system_context(clean_input)
        prompt = (
            f"{sys_context}\n\n"
            f"REGLA: Responde en 1 o máximo 2 oraciones directas sin saludos ni relleno.\n"
            f"Pregunta: {clean_input}\n"
            f"Respuesta:"
        )
        response = self._get_llm_response(clean_input, prompt)
        
        # Mantener historial acotado a 6 líneas
        self.chat_history += f"Usuario: {clean_input}\nJARVIS: {response}\n"
        lines = self.chat_history.split("\n")
        if len(lines) > 6:
            self.chat_history = "\n".join(lines[-6:])
            
        return response

    def _reset_pending(self):
        self.pending_action = None
        self.pending_service = None
        self.pending_value = None
        self.awaiting_update_confirm = False

    def close(self):
        if hasattr(self.memory_manager, 'close'):
            self.memory_manager.close()