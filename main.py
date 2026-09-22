from core.jarvis import Jarvis
from core.router import JarvisRouter


def main():
    print("🤖 JARVIS [Clean Architecture] Inicializado y Operativo.\n")

    router = JarvisRouter()
    jarvis = Jarvis(router=router)

    saludo = router.greet_user()
    print(f"JARVIS: {saludo}\n")

    try:
        while True:
            user_input = input("Tú: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\nJARVIS: A su servicio siempre, Creador. Hasta pronto.\n")
                break

            response = jarvis.process(user_input)

            if response:
                print(f"JARVIS: {response}\n")

    except KeyboardInterrupt:
        print("\n\nSesión interrumpida por el usuario. Hasta luego, Creador.")

    finally:
        router.close()


if __name__ == "__main__":
    main()