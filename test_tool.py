from tools.code_search import CodeSearchTool

search_tool = CodeSearchTool()
print("🔍 Probando tgrep desde Python...")
resultado = search_tool.search_code("MemoryManager")

print("\n--- RESULTADO DE TGREP ---")
print(resultado)
