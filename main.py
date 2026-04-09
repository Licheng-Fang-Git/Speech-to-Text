import os
from dotenv import load_dotenv
import json
import queue
import sounddevice as sd
import websocket
import threading

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

SAMPLE_RATE = 16000
CHANNELS = 1

audio_queue = queue.Queue()

# Capture microphone audio
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.tobytes())

# Handle Deepgram messages
def on_message(ws, message):
    data = json.loads(message)

    if "channel" in data:
        alternatives = data["channel"]["alternatives"][0]
        transcript = alternatives.get("transcript", "")

        if transcript:
            # interim = live partial text
            if data.get("is_final"):
                print(f"\n {transcript}")
                with open("output.txt", "w") as file:
                    file.write(transcript)
            else:
                print(f"\r {transcript}", end="", flush=True)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("\n Connection closed")

def on_open(ws):
    print("Connected to Deepgram")

    def send_audio():
        while True:
            data = audio_queue.get()
            ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

    threading.Thread(target=send_audio, daemon=True).start()

# 🔗 Start WebSocket connection
def start():
    url = (
        "wss://api.deepgram.com/v1/listen?"
        "model=nova-3&"
        "encoding=linear16&"
        "sample_rate=16000&"
        "channels=1&"
        "interim_results=true&"   
        "punctuate=true"
    )

    headers = [
        f"Authorization: Token {DEEPGRAM_API_KEY}"
    ]

    ws = websocket.WebSocketApp(
        url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # Start mic
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        callback=audio_callback,
    ):
        ws.run_forever()

if __name__ == "__main__":
    print("Starting live captions...")
    start()

#pip install sounddevice websocket-client numpy
#pip install python-dotenv