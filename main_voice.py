import sys
from core.router import JarvisRouter
from infrastructure.audio_engine import AudioEngine

def main():
    print("🤖 JARVIS [Modo Voz Activo] Inicializado.")
    router = JarvisRouter()
    audio = AudioEngine()

    # Saludo único solo al arrancar la aplicación
    saludo = "Sistemas listos. Te escucho, creador."
    print(f"\nJARVIS: {saludo}")
    audio.speak(saludo)

    try:
        while True:
            # 1. Escuchar micrófono
            user_text = audio.listen_and_transcribe(duration=4)
            
            # Si no hay voz captada, se omite silenciosamente sin hablar
            if not user_text or len(user_text) < 2:
                continue

            print(f"\nTú (Voz): {user_text}")

            # Comandos de salida
            if any(cmd in user_text.lower() for cmd in ["salir", "adios", "adiós", "apagate", "apágate"]):
                despedida = "Entendido. Apagando sistemas de voz."
                print(f"\nJARVIS: {despedida}")
                audio.speak(despedida)
                break

            # 2. Procesar respuesta
            response_text = router.process_message(user_text)

            # 3. Reproducir respuesta hablada sin saludos redundantes
            if response_text:
                audio.speak(response_text)

    except KeyboardInterrupt:
        print("\n\nSesión de voz interrumpida por teclado.")
    finally:
        router.close()

if __name__ == "__main__":
    main()