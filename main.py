import os
import maniac
from discord.ext import commands
from pydub.utils import which
os.environ["PATH"] += os.pathsep + which("ffmpeg")
from server import keep_alive




if __name__ == "__main__":
    keep_alive()
    maniac.run_bot()
