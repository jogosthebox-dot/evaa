import speech_recognition as sr


MICROFONE = 1

recognizer = sr.Recognizer()

print("🎤 Preparando o microfone...")

with sr.Microphone(device_index=MICROFONE) as source:
    print("🔧 Ajustando o ruído ambiente...")

    recognizer.adjust_for_ambient_noise(
        source,
        duration=1
    )

    print()
    print("🎤 PODE FALAR!")
    print("Fale uma frase normalmente.")
    print()

    audio = recognizer.listen(
        source,
        timeout=10,
        phrase_time_limit=8
    )

print("🧠 Entendendo o que você falou...")

try:
    texto = recognizer.recognize_google(
        audio,
        language="pt-BR"
    )

    print()
    print("✅ Eva entendeu:")
    print(texto)

except sr.UnknownValueError:
    print()
    print("❌ Não consegui entender o que foi dito.")

except sr.RequestError as error:
    print()
    print("❌ Erro ao acessar o reconhecimento de voz:")
    print(error)

except Exception as error:
    print()
    print("❌ Erro:")
    print(error)