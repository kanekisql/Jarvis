import chromadb
from config.settings import DB_PATH

client = chromadb.PersistentClient(path=DB_PATH)
collections = ["user_profile", "secrets_vault", "project_knowledge", "general_memory"]

print("=== CONTENIDO DE LA MEMORIA VECTORIAL ===\n")
for col_name in collections:
    col = client.get_or_create_collection(name=col_name)
    data = col.get()
    print(f"📁 Colección: [{col_name}] (Total: {col.count()})")
    if data and data.get("documents"):
        for doc_id, doc in zip(data["ids"], data["documents"]):
            print(f"   • ID: {doc_id} | Contenido: {doc}")
    else:
        print("   (Vacía)")
    print("-" * 50)