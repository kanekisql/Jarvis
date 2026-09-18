import os
import json
import uuid
from datetime import datetime
from config.settings import PROFILE_PATH
from infrastructure.vector_db import VectorMemory

class MemoryManager:
    def __init__(self):
        self.vector_db = VectorMemory()
        self.profile = self._load_profile()

    def _load_profile(self) -> dict:
        if not os.path.exists(PROFILE_PATH):
            default_profile = {
                "nombre_usuario": "Estheban Andre",
                "ubicacion": "Chorrillos, Lima, Perú",
                "os": "Kali Linux"
            }
            os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(default_profile, f, indent=4, ensure_ascii=False)
            return default_profile
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_secret_intent(self, text: str) -> bool:
        text_lower = text.lower()
        synonyms = ["secreto", "clave", "password", "contraseña", "token", "credencial", "pass", "pin", "acceso"]
        return any(kw in text_lower for kw in synonyms)

    def save_secret(self, service: str, value: str):
        self.vector_db.save_secret_exact(service, value)

    def get_secret(self, service: str) -> str:
        return self.vector_db.get_secret_exact(service)

    def save_memory(self, text: str, category: str = "general") -> str:
        doc_id = str(uuid.uuid4())
        self.vector_db.add_memory(text=text, doc_id=doc_id, category=category)
        return category

    def get_system_context(self, current_query: str) -> str:
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        recuerdos = self.vector_db.query_memories(current_query)
        recuerdos_filtrados = [r for r in recuerdos.split("\n") if "Secreto" not in r and "contraseña" not in r.lower()] if recuerdos else []
        
        return (
            f"[REGLAS DE ACTUACIÓN]:\n"
            f"- Eres JARVIS, un asistente conciso, técnico y directo.\n"
            f"- Responde en 1 o máximo 2 oraciones breves la consulta actual.\n"
            f"- NO hagas comentarios meta ni digas que ya respondiste antes.\n"
            f"DATOS DEL USUARIO: Nombre: {self.profile.get('nombre_usuario')}, OS: {self.profile.get('os')}.\n"
            f"FECHA/HORA SISTEMA: {hora_actual}\n"
            f"MEMORIA RELEVANTE: {' '.join(recuerdos_filtrados) if recuerdos_filtrados else 'Ninguna'}"
        )

    def close(self):
        pass