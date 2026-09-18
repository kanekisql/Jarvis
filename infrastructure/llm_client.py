import requests
import json
from config.settings import OLLAMA_URL, MODEL_NAME

class OllamaClient:
    def __init__(self, model: str = MODEL_NAME):
        self.model = model
        self.url = OLLAMA_URL

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nUsuario: {prompt}\nJARVIS:",
            "stream": True
        }
        
        try:
            response = requests.post(self.url, json=payload, stream=True)
            if response.status_code == 200:
                texto_completo = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        fragmento = chunk.get("response", "")
                        yield fragmento
                        texto_completo += fragmento
            else:
                yield f"Error HTTP {response.status_code}"
        except Exception as e:
            yield f"Error de conexión con Ollama: {e}"