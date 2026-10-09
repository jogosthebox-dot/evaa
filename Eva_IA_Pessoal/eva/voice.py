import re
import threading

import pyttsx3
import sounddevice as sd
import speech_recognition as sr


class Voice:

    def __init__(self):
        self.lock = threading.Lock()

        self.rate = 175
        self.volume = 1.0
        self.voice_id = None

        # Microfone Realtek detectado no teste
        self.microphone_index = 1

        # Reconhecimento de voz
        self.recognizer = sr.Recognizer()

        # Descobre a voz em português disponível no Windows
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")

            if voices:
                for voice in voices:
                    name = str(
                        getattr(voice, "name", "")
                    ).lower()

                    languages = str(
                        getattr(voice, "languages", "")
                    ).lower()

                    if (
                        "brazil" in name
                        or "portugu" in name
                        or "pt-br" in name
                        or "pt" in languages
                    ):
                        self.voice_id = voice.id
                        break

            engine.stop()

        except Exception as e:
            print(
                f"[Voz] Erro ao inicializar: {e}"
            )

    def clean_for_speech(self, text):
        text = str(text)

        text = re.sub(
            r"```.*?```",
            " ",
            text,
            flags=re.DOTALL
        )

        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text
        )

        text = re.sub(
            r"^\s*#{1,6}\s*",
            "",
            text,
            flags=re.MULTILINE
        )

        text = text.replace("**", "")
        text = text.replace("__", "")
        text = text.replace("*", "")
        text = text.replace("_", " ")

        text = re.sub(
            r"^\s*[-•]\s+",
            "",
            text,
            flags=re.MULTILINE
        )

        text = re.sub(
            r"^\s*>\s?",
            "",
            text,
            flags=re.MULTILINE
        )

        replacements = [
            (r"(?<!\w)km/h(?!\w)", " quilômetros por hora "),
            (r"(?<!\w)°C(?!\w)", " graus Celsius "),
            (r"(?<!\w)°F(?!\w)", " graus Fahrenheit "),
            (r"R\$", " reais "),
            (r"(?<!\w)GB(?!\w)", " gigabytes "),
            (r"(?<!\w)MB(?!\w)", " megabytes "),
            (r"(?<!\w)KB(?!\w)", " kilobytes "),
            (r"(?<!\w)TB(?!\w)", " terabytes "),
            (r"(?<!\w)FPS(?!\w)", " FPS "),
            (r"(?<!\w)kg(?!\w)", " quilos "),
            (r"(?<!\w)km(?!\w)", " quilômetros "),
            (r"(?<!\w)cm(?!\w)", " centímetros "),
            (r"(?<!\w)mm(?!\w)", " milímetros "),
            (r"(?<!\w)g(?!\w)", " gramas "),
        ]

        for pattern, replacement in replacements:
            text = re.sub(
                pattern,
                replacement,
                text,
                flags=re.IGNORECASE
            )

        symbol_replacements = {
            "%": " por cento ",
            "&": " e ",
            "+": " mais ",
            "=": " igual ",
        }

        for symbol, replacement in symbol_replacements.items():
            text = text.replace(
                symbol,
                replacement
            )

        text = re.sub(
            r"[^\w\sÀ-ÿ.,!?;:%()\-]",
            " ",
            text,
            flags=re.UNICODE
        )

        text = text.replace(
            "(",
            " "
        )

        text = text.replace(
            ")",
            " "
        )

        text = re.sub(
            r"\s-\s",
            " ",
            text
        )

        text = re.sub(
            r"([!?.,;])\1+",
            r"\1",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    def speak(self, text):
        if not text:
            return

        original_text = str(text).strip()

        if not original_text:
            return

        speech_text = self.clean_for_speech(
            original_text
        )

        if not speech_text:
            return

        with self.lock:
            engine = None

            try:
                engine = pyttsx3.init()

                engine.setProperty(
                    "rate",
                    self.rate
                )

                engine.setProperty(
                    "volume",
                    self.volume
                )

                if self.voice_id:
                    try:
                        engine.setProperty(
                            "voice",
                            self.voice_id
                        )
                    except Exception:
                        pass

                print(
                    f"🔊 Eva: {speech_text}"
                )

                engine.say(
                    speech_text
                )

                engine.runAndWait()

            except Exception as e:
                print(
                    f"[Voz] Erro ao falar: {e}"
                )

            finally:
                if engine:
                    try:
                        engine.stop()
                    except Exception:
                        pass

    def listen_and_transcribe(
        self,
        seconds=8
    ):
        print()
        print("🎤 Eva está ouvindo...")

        try:
            with sr.Microphone(
                device_index=self.microphone_index
            ) as source:

                print(
                    "🔧 Ajustando o ruído ambiente..."
                )

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5
                )

                print(
                    "🎤 Pode falar..."
                )

                audio = self.recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=seconds
                )

            print(
                "🧠 Entendendo..."
            )

            text = self.recognizer.recognize_google(
                audio,
                language="pt-BR"
            )

            print(
                f"🎤 Você: {text}"
            )

            return text

        except sr.WaitTimeoutError:
            print(
                "[Microfone] Nenhuma fala detectada."
            )

            return ""

        except sr.UnknownValueError:
            print(
                "[Microfone] Não consegui entender."
            )

            return ""

        except sr.RequestError as error:
            print(
                f"[Microfone] Erro no reconhecimento: {error}"
            )

            return ""

        except Exception as error:
            print(
                f"[Microfone] Erro: {error}"
            )

            return ""