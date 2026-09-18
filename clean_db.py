from infrastructure.vector_db import VectorMemory

memory = VectorMemory()

# Borrar datos de prueba/preguntas en secrets_vault
secrets_col = memory.collections["secrets"]
all_secrets = secrets_col.get()

# Conservar solo los que realmente contienen información/claves útiles
ids_to_delete = []
for doc_id, doc in zip(all_secrets["ids"], all_secrets["documents"]):
    # Si el documento es una pregunta, lo marcamos para borrar
    if "?" in doc or "cual es" in doc.lower() or "cuál es" in doc.lower():
        ids_to_delete.append(doc_id)

if ids_to_delete:
    secrets_col.delete(ids=ids_to_delete)
    print(f"Se eliminaron {len(ids_to_delete)} registros inservibles de 'secrets_vault'.")
else:
    print("No se encontraron preguntas en 'secrets_vault'.")