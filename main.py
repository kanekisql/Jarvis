import sys
from core.router import JarvisRouter

def main():
    print("🤖 JARVIS [Clean Architecture] Inicializado y Operativo.\n")
    router = JarvisRouter()
    
    # JARVIS toma la iniciativa y saluda primero al iniciar
    router.greet_user()

    try:
        while True:
            user_input = input("Tú: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\nJARVIS: A su servicio siempre, Creador. Hasta pronto.\n")
                break
                
            # CAPTURAR E IMPRIMIR LA RESPUESTA
            response = router.process_message(user_input)
            print(f"JARVIS: {response}\n")
            
    except KeyboardInterrupt:
        print("\n\nSesión interrumpida por el usuario. Hasta luego, Creador.")
    finally:
        router.close()

if __name__ == "__main__":
    main()