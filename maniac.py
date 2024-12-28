import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('token')
    intents = discord.Intents.all()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    voice_clients = {}
    yt_dl_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)
    
    ffmpeg = {'options': '-vn'}

    # สร้างคิวเพลง
    song_queue = {}

    async def play_next(ctx):
        if song_queue.get(ctx.guild.id):
            song = song_queue[ctx.guild.id].pop(0)  # เอาเพลงแรกออกจากคิว
            player = discord.FFmpegPCMAudio(song['url'], **ffmpeg)
            voice_clients[ctx.guild.id].play(player, after=lambda e: play_next(ctx))

    @client.event
    async def on_ready():
        print(f"{client.user} is now online")
        
    @client.event
    async def on_message(message):
        if message.content.startswith("?play"):
            try:
                # เชื่อมต่อกับช่องเสียง
                channel = message.author.voice.channel
                voice_client = await channel.connect()
                voice_clients[message.guild.id] = voice_client
                
                # ปิดหูฟังตัวเอง (deaf)
                await voice_client.guild.me.edit(deafen=True)

            except Exception as e:
                print(f"Error connecting to voice channel: {e}")
        
            try:
                url = message.content.split()[1]
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                song_url = data['url']
                song_info = {'url': song_url}

                # เพิ่มเพลงลงในคิว
                if message.guild.id not in song_queue:
                    song_queue[message.guild.id] = []
                song_queue[message.guild.id].append(song_info)

                # เริ่มเล่นเพลงถ้าคิวว่าง
                if not voice_clients[message.guild.id].is_playing():
                    await play_next(message)

            except Exception as e:
                print(f"Error playing the song: {e}")

        elif message.content.startswith("?skip"):
            # ข้ามเพลง
            voice_client = voice_clients.get(message.guild.id)
            if voice_client and voice_client.is_playing():
                voice_client.stop()  # หยุดการเล่นเพลงปัจจุบัน
                await message.channel.send("Song skipped!")
                await play_next(message)

        elif message.content.startswith("?resume"):
            # ดำเนินการต่อจากเพลงที่หยุด
            voice_client = voice_clients.get(message.guild.id)
            if voice_client and not voice_client.is_playing():
                await message.channel.send("Resuming song!")
                await play_next(message)

        elif message.content.startswith("?pause"):
            # หยุดการเล่นเพลง
            voice_client = voice_clients.get(message.guild.id)
            if voice_client and voice_client.is_playing():
                voice_client.pause()  # หยุดการเล่นเพลงชั่วคราว
                await message.channel.send("Song paused!")

        elif message.content.startswith("?stop"):
            # หยุดเพลงและตัดการเชื่อมต่อ
            voice_client = voice_clients.get(message.guild.id)
            if voice_client:
                voice_client.stop()
                await voice_client.disconnect()
                del voice_clients[message.guild.id]
                del song_queue[message.guild.id]
                await message.channel.send("Disconnected and stopped the music.")

        elif message.content.startswith("?queue"):
            # แสดงคิวเพลง
            if message.guild.id in song_queue and song_queue[message.guild.id]:
                queue_list = "\n".join([f"{idx + 1}. {song['url']}" for idx, song in enumerate(song_queue[message.guild.id])])
                await message.channel.send(f"Current queue:\n{queue_list}")
            else:
                await message.channel.send("The queue is empty.")
        
        elif message.content.startswith("?loop"):
            voice_client = voice_clients.get(message.guild.id)
            if voice_client and voice_client.is_playing():
                # หยุดการเล่นเพลงก่อน
                voice_client.stop()
            
                # ดึงเพลงที่กำลังเล่นอยู่ในตอนนี้จากคิว
                current_song = song_queue[message.guild.id][0]  # สมมุติว่าเพลงแรกในคิวเป็นเพลงที่เล่นอยู่
            
                # เริ่มเล่นเพลงซ้ำ
                loop_song = discord.FFmpegPCMAudio(current_song['url'], **ffmpeg)
                voice_client.play(loop_song, after=lambda e: after_song_played(message))
            
                await message.channel.send(f"Looping: {current_song['url']}")
            else:
                await message.channel.send("No song is currently playing.")

        # คำสั่ง ?help
        elif message.content.startswith("?help"):
            embed = discord.Embed(
                title="Bot Commands",
                description="Here are the available commands for the bot:",
                color=discord.Color.blue()
            )
            embed.add_field(name="?play <URL>", value="Play a song from YouTube", inline=False)
            embed.add_field(name="?skip", value="Skip the current song", inline=False)
            embed.add_field(name="?resume", value="Resume the current song", inline=False)
            embed.add_field(name="?pause", value="Pause the current song", inline=False)
            embed.add_field(name="?stop", value="Stop the music and disconnect", inline=False)
            embed.add_field(name="?queue", value="Show the current song queue", inline=False)
            embed.add_field(name="?help", value="Show this help message", inline=False)

            await message.channel.send(embed=embed)
            
    def after_song_played(message):
        voice_client = voice_clients.get(message.guild.id)
        if voice_client:
            # สั่งให้เพลงเล่นซ้ำทันที
            current_song = song_queue[message.guild.id][0]
            loop_song = discord.FFmpegPCMAudio(current_song['url'], **ffmpeg)
            voice_client.play(loop_song, after=lambda e: after_song_played(message))

    client.run(TOKEN)
