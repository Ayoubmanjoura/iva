import subprocess


def play_mp3_bytes(mp3_bytes_io):
    proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-"],
        stdin=subprocess.PIPE,
    )
    proc.communicate(input=mp3_bytes_io.read())