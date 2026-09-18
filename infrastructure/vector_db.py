import os
import json
import chromadb
from config.settings import DB_PATH, BASE_DIR

SECRETS_FILE = os.path.join(BASE_DIR, "data", "secrets_vault.json")

class VectorMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_PATH)
        
        self.collections = {
            "profile": self.client.get_or_create_collection(name="user_profile"),
            "secrets": self.client.get_or_create_collection(name="secrets_vault"),
            "projects": self.client.get_or_create_collection(name="project_knowledge"),
            "general": self.client.get_or_create_collection(name="general_memory")
        }
        self._init_secrets_file()

    def _init_secrets_file(self):
        """Asegura que exista la bóveda JSON de claves exactas."""
        os.makedirs(os.path.dirname(SECRETS_FILE), exist_ok=True)
        if not os.path.exists(SECRETS_FILE):
            with open(SECRETS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4, ensure_ascii=False)

    def save_secret_exact(self, service: str, value: str):
        """Guarda una clave exacta en la bóveda estructurada."""
        service_clean = service.lower().strip()
        with open(SECRETS_FILE, "r", encoding="utf-8") as f:
            secrets = json.load(f)
        
        secrets[service_clean] = value
        
        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            json.dump(secrets, f, indent=4, ensure_ascii=False)
            
        # Opcional: También guardar en ChromaDB
        self.add_memory(f"Servicio: {service_clean} | Clave: {value}", doc_id=f"secret_{service_clean}", category="secrets")

    def get_secret_exact(self, service: str) -> str:
        """Recupera la clave exacta sin alucinaciones vectoriales."""
        service_clean = service.lower().strip()
        if os.path.exists(SECRETS_FILE):
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                secrets = json.load(f)
            # Buscar coincidencia exacta o parcial de servicio
            for k, v in secrets.items():
                if k in service_clean or service_clean in k:
                    return v
        return None

    def add_memory(self, text: str, doc_id: str, category: str = "general"):
        target_collection = self.collections.get(category, self.collections["general"])
        target_collection.add(documents=[text], ids=[doc_id])

    def query_memories(self, query: str, category: str = None, top_k: int = 3) -> str:
        if category and category in self.collections:
            collections_to_search = [category]
        else:
            collections_to_search = ["general", "profile"]

        results_text = []
        for cat in collections_to_search:
            col = self.collections[cat]
            if col.count() > 0:
                res = col.query(query_texts=[query], n_results=min(top_k, col.count()))
                docs = res.get("documents", [[]])[0]
                results_text.extend(docs)

        return "\n".join(results_text)