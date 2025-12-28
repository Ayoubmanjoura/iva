# import sounddevice as sd
# import queue
# import json
# import time
# import collections
# import webrtcvad
# from vosk import Model, KaldiRecognizer


# def speech_to_text(model_path, samplerate=16000, silence_timeout=2.0):
#     model = Model(model_path)
#     recognizer = KaldiRecognizer(model, samplerate)

#     vad = webrtcvad.Vad(2)  # 0–3 (higher = stricter)
#     q = queue.Queue()
#     final_text = ""

#     frame_duration_ms = 30
#     frame_size = int(samplerate * frame_duration_ms / 1000)
#     bytes_per_frame = frame_size * 2  # int16

#     ring_buffer = collections.deque(maxlen=10)
#     triggered = False
#     last_speech_time = time.time()

#     def callback(indata, frames, time_info, status):
#         if status:
#             print(status)
#         q.put(bytes(indata))

#     with sd.RawInputStream(
#         samplerate=samplerate,
#         blocksize=frame_size,
#         dtype="int16",
#         channels=1,
#         callback=callback,
#     ):
#         print("Listening...")

#         while True:
#             data = q.get()
#             now = time.time()

#             if len(data) < bytes_per_frame:
#                 continue

#             is_speech = vad.is_speech(data, samplerate)

#             if is_speech:
#                 last_speech_time = now

#             if not triggered:
#                 ring_buffer.append((data, is_speech))
#                 voiced = sum(1 for _, s in ring_buffer if s)

#                 if voiced > 0.7 * ring_buffer.maxlen:
#                     triggered = True
#                     for d, _ in ring_buffer:
#                         recognizer.AcceptWaveform(d)
#                     ring_buffer.clear()

#             else:
#                 recognizer.AcceptWaveform(data)
#                 ring_buffer.append((data, is_speech))
#                 unvoiced = sum(1 for _, s in ring_buffer if not s)

#                 if unvoiced > 0.7 * ring_buffer.maxlen:
#                     triggered = False
#                     ring_buffer.clear()

#                     result = json.loads(recognizer.Result())
#                     text = result.get("text", "").strip()
#                     if text:
#                         final_text += text + " "
#                         print("FINAL:", text)

#             if now - last_speech_time > silence_timeout:
#                 print("Silence detected. Done.")
#                 break

#     return final_text.strip()
import sounddevice as sd
import queue
import time
import collections
from faster_whisper import WhisperModel
import webrtcvad

def speech_to_text_faster_whisper(model_size="small", samplerate=16000, silence_timeout=2.0):
    # Load faster-whisper model
    model = WhisperModel(model_size)

    # VAD setup
    vad = webrtcvad.Vad(2)  # 0-3 aggressive
    q = queue.Queue()
    frame_duration_ms = 30
    frame_size = int(samplerate * frame_duration_ms / 1000)
    bytes_per_frame = frame_size * 2  # int16
    ring_buffer = collections.deque(maxlen=10)
    triggered = False
    last_speech_time = time.time()
    final_audio = bytearray()

    # Audio callback
    def callback(indata, frames, time_info, status):
        if status:
            print(status)
        q.put(bytes(indata))

    print("Listening...")
    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=frame_size,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        while True:
            data = q.get()
            now = time.time()
            if len(data) < bytes_per_frame:
                continue

            is_speech = vad.is_speech(data, samplerate)

            if is_speech:
                last_speech_time = now

            if not triggered:
                ring_buffer.append((data, is_speech))
                voiced = sum(1 for _, s in ring_buffer if s)
                if voiced > 0.7 * ring_buffer.maxlen:
                    triggered = True
                    for d, _ in ring_buffer:
                        final_audio.extend(d)
                    ring_buffer.clear()
            else:
                final_audio.extend(data)
                ring_buffer.append((data, is_speech))
                unvoiced = sum(1 for _, s in ring_buffer if not s)
                if unvoiced > 0.7 * ring_buffer.maxlen:
                    triggered = False
                    ring_buffer.clear()

            if now - last_speech_time > silence_timeout and final_audio:
                break

    # faster-whisper expects float32 numpy array
    import numpy as np
    audio_np = np.frombuffer(final_audio, dtype=np.int16).astype(np.float32) / 32768.0

    # Transcribe
    segments, info = model.transcribe(audio_np, beam_size=5)
    final_text = ""
    for segment in segments:
        final_text += segment.text + " "

    return final_text.strip()


if __name__ == "__main__":
    text = speech_to_text_faster_whisper()
    print("FINAL TRANSCRIPTION:", text)
