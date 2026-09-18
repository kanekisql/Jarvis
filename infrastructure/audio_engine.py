import os
import tempfile
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
from gtts import gTTS

class AudioEngine:
    def __init__(self):
        print("🎙️ Cargando modelo de voz Whisper...")
        self.whisper = WhisperModel("tiny", device="cpu", compute_type="int8")

    def speak(self, text: str):
        if not text.strip():
            return
        try:
            tts = gTTS(text=text, lang='es', slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_filename = fp.name
                tts.save(temp_filename)
            
            res = os.system(f"paplay '{temp_filename}' 2>/dev/null")
            if res != 0:
                res = os.system(f"mpg123 -q '{temp_filename}' 2>/dev/null")
            if res != 0:
                os.system(f"ffplay -nodisp -autoexit -loglevel quiet '{temp_filename}' 2>/dev/null")

            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        except Exception as e:
            print(f"\n[Error de Audio TTS]: {e}")

    def listen_and_transcribe(self, duration=4, samplerate=16000) -> str:
        """Graba audio, valida que haya voz real (evitando alucinaciones) y transcribe."""
        print("\n🎤 Escuchando...")
        try:
            # Grabación a 16000 Hz (frecuencia nativa óptima para Whisper)
            audio_data = sd.rec(
                int(duration * samplerate),
                samplerate=samplerate,
                channels=1,
                dtype='int16'
            )
            sd.wait()

            # --- CONTROL DE SILENCIO / ENERGÍA DE AUDIO ---
            # Calcular el nivel de volumen/energía (RMS)
            audio_float = audio_data.astype(np.float32)
            rms = np.sqrt(np.mean(audio_float**2))
            
            # Si el nivel es muy bajo, asumimos silencio y evitamos llamar a Whisper
            # Ajusta 200 a un valor más bajo si hablas muy despacio (ej. 100)
            if rms < 200:
                return ""

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
                temp_wav = fp.name
                write(temp_wav, samplerate, audio_data)

            # Prompts léxicos y forzado de idioma español
            prompt_guia = "Jarvis, Estheban, React, GitHub, contraseña, clave, 7227, eli, hora, dólar."
            segments, _ = self.whisper.transcribe(
                temp_wav,
                language="es",
                task="transcribe",
                initial_prompt=prompt_guia,
                condition_on_previous_text=False # Evita bucles repetitivos como "si, si, si"
            )
            transcription = " ".join([segment.text for segment in segments]).strip()
            
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

            return transcription

        except Exception as e:
            print(f"\n[Error de captura de micrófono]: {e}")
            return ""