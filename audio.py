import subprocess
import sys


def play_mp3_bytes(mp3_bytes_io):
    proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-"],
        stdin=subprocess.PIPE,
    )

    proc.stdin.write(mp3_bytes_io.read())
    proc.stdin.close()
    proc.wait()
