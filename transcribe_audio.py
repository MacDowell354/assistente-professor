import openai
import os

# Certifique-se de que sua variável OPENAI_API_KEY esteja configurada no Render
openai.api_key = os.getenv("OPENAI_API_KEY")

AUDIO_PATH = "audio.opus"  # renomeie seu arquivo .opus para esse nome no render

def transcrever_audio():
    try:
        with open(AUDIO_PATH, "rb") as audio_file:
            print("Enviando para transcrição...")
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language="pt",
                response_format="text"
            )
            print("🔊 Transcrição concluída com sucesso:\n")
            print(response)
    except Exception as e:
        print(f"❌ Erro ao transcrever: {e}")

if __name__ == "__main__":
    transcrever_audio()
