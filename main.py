import os
import maniac
from discord.ext import commands
from pydub.utils import which
os.environ["PATH"] += os.pathsep + which("ffmpeg")
from server import server_on


if __name__ == "__main__":
    maniac.run_bot()
    server_on()
