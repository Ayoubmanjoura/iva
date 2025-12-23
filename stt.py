import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer


def speech_to_text(model_path, samplerate=16000):
    model = Model(model_path)
    q = queue.Queue()
    final_text = ""

    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(bytes(indata))

    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        print("Listening... Ctrl+C to stop")
        rec = KaldiRecognizer(model, samplerate)

        try:
            while True:
                data = q.get()

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        final_text += text + " "
                        print("FINAL:", text)

        except KeyboardInterrupt:
            print("\nStopped listening.")

    return final_text.strip()
