import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "jarvis_memory_db")
PROFILE_PATH = os.path.join(BASE_DIR, "user_profile.json")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"