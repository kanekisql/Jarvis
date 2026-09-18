import subprocess
import os
import shutil

class CodeSearchTool:
    def __init__(self, target_directory: str = "."):
        """
        Inicializa la herramienta apuntando al directorio raíz del proyecto JARVIS.
        """
        self.target_directory = os.path.abspath(target_directory)
        # Definimos la ruta absoluta de tgrep basada en tu sistema
        self.tgrep_path = os.path.expanduser("~/.cargo/bin/tgrep")

    def search_code(self, query: str) -> str:
        """
        Ejecuta tgrep para buscar un patrón o texto dentro de los archivos de código.
        """
        # Verificamos si existe el ejecutable directo en ~/.cargo/bin/tgrep
        if os.path.exists(self.tgrep_path):
            cmd = [self.tgrep_path, "search", query]
        elif shutil.which("tgrep"):
            cmd = ["tgrep", "search", query]
        else:
            ## Si usas grep como fallback, excluye carpetas ruidosas
            cmd = [
                "grep",
                "-rnI",
                "--exclude-dir={env,.venv,__pycache__,.git,node_modules}",
                query,
                ".",
            ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.target_directory,
                capture_output=True,
                text=True,
                check=False
            )
            
            output = result.stdout.strip()
            if not output:
                return f"No se encontraron coincidencias para '{query}' en el código."
            
            return output
        except Exception as e:
            return f"Error al ejecutar la búsqueda de código: {str(e)}"
