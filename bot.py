import discord
from discord.ext import tasks
from mcstatus import JavaServer
from datetime import datetime, timezone
import asyncio
import os

# ==================== CONFIGURATIE ====================
TOKEN = os.getenv("MTU2NTUyNDQ5MDY4MTcxNjg5Ng.Gn5Lq_.0x1iqobDLWnz4LuYT-zcVKnXLq8KWjmgfW8Qy8")
CHANNEL_ID = int(os.getenv("1559166662639493231"))
MC_HOST = os.getenv("MC_HOST", "play.pirate-smp.nl")
MC_PORT = int(os.getenv("MC_PORT", "25779"))
SERVER_NAME = os.getenv("SERVER_NAME", "Pirate SMP")
UPDATE_INTERVAL = 15
# =====================================================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

status_message = None
last_was_online = None
last_restart = None


def create_embed(online: bool, players_online=0, players_max=0, latency=0, version=None, motd=None):
    if online:
        color = discord.Color.green()
        title = f"🟢 {SERVER_NAME} — Online"
        status_text = "Online"
    else:
        color = discord.Color.red()
        title = f"🔴 {SERVER_NAME} — Offline"
        status_text = "Offline"

    embed = discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Status", value=status_text, inline=True)

    if online:
        embed.add_field(name="Spelers", value=f"**{players_online}** / {players_max}", inline=True)
        embed.add_field(name="Ping", value=f"**{latency:.0f}** ms", inline=True)
        if version:
            embed.add_field(name="Versie", value=version, inline=True)
        if motd:
            clean_motd = ''.join(c for c in str(motd) if ord(c) < 128 or c.isprintable())
            embed.add_field(name="MOTD", value=clean_motd[:100], inline=False)
    else:
        embed.add_field(name="Spelers", value="—", inline=True)
        embed.add_field(name="Ping", value="—", inline=True)

    if last_restart:
        embed.add_field(name="Laatste restart", value=f"<t:{int(last_restart.timestamp())}:R>", inline=False)

    embed.set_footer(text=f"Live update elke {UPDATE_INTERVAL} seconden")
    return embed


@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_status():
    global status_message, last_was_online, last_restart

    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Kanaal niet gevonden!")
        return

    online = False
    players_online = 0
    players_max = 0
    latency = 0
    version = None
    motd = None

    try:
        server = JavaServer(MC_HOST, MC_PORT)
        status = await asyncio.wait_for(asyncio.to_thread(server.status), timeout=10.0)

        online = True
        players_online = status.players.online
        players_max = status.players.max
        latency = status.latency
        version = status.version.name if status.version else None
        motd = status.motd

    except Exception as e:
        online = False
        print(f"Server offline of fout: {e}")

    if last_was_online is False and online is True:
        last_restart = datetime.now(timezone.utc)
        print("Server is zojuist herstart!")

    last_was_online = online

    embed = create_embed(online, players_online, players_max, latency, version, motd)

    try:
        if status_message is None:
            status_message = await channel.send(embed=embed)
            print("Nieuwe status message aangemaakt")
        else:
            await status_message.edit(embed=embed)
    except Exception as e:
        print(f"Fout bij updaten bericht: {e}")
        status_message = None


@client.event
async def on_ready():
    print(f"Bot is online als {client.user}")
    update_status.start()


client.run(TOKEN)
