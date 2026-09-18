import pyttsx3

print("🔊 Probando altavoz con pyttsx3...")
engine = pyttsx3.init()

# Ajustar velocidad (palabras por minuto) y volumen
engine.setProperty('rate', 165)
engine.setProperty('volume', 1.0)

# Mensaje de prueba
engine.say("Inicializando sistemas de voz. Buenas tardes, creador.")
engine.runAndWait()

print("✅ Prueba finalizada.")

