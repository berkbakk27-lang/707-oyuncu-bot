import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime
import asyncio

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Bot Sistemi Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

TOKEN = os.getenv('PLAYER_BOT_TOKEN') 
FIVEM_IP = "185.211.100.221:30120"
DUYURU_KANAL_ID = 1491175628354097314

last_status = None

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label='Destek Talebi Aç', style=discord.ButtonStyle.success, emoji='📩', custom_id='ticket_btn')
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}")
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"✅ Biletin açıldı: {channel.mention}", ephemeral=True)
        await channel.send(f"👋 {interaction.user.mention} Hoş geldin! Kapatmak için: `!kapat` yazabilirsin.")

@tasks.loop(seconds=60)
async def check_server_status():
    global last_status
    channel = bot.get_channel(DUYURU_KANAL_ID)
    if not channel: return
    try:
        r = requests.get(f"http://{FIVEM_IP}/info.json", timeout=5)
        current_status = "online" if r.status_code == 200 else "offline"
    except: current_status = "offline"
    if last_status is not None and current_status != last_status:
        color = 0x2ecc71 if current_status == "online" else 0xe74c3c
        status_text = "AKTİF" if current_status == "online" else "KAPALI"
        embed = discord.Embed(title=f"🚀 PROJECT GUN {status_text}", color=color, timestamp=datetime.now())
        await channel.send(embed=embed)
    last_status = current_status

@bot.command()
async def botyardım(ctx):
    embed = discord.Embed(title="🤖 707 Komut Paneli", color=0xf1c40f)
    embed.add_field(name="🚀 Sunucu", value="`!sunucu`, `!oyuncusayi`", inline=False)
    embed.add_field(name="🎫 Destek", value="`!ticket`, `!kapat`", inline=False)
    embed.add_field(name="🛠️ Genel", value="`!clear`, `!steam`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ticket(ctx):
    await ctx.send(embed=discord.Embed(title="🎫 DESTEK", description="Butona tıkla.", color=0x3498db), view=TicketView())

@bot.command()
async def sunucu(ctx):
    try:
        r = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5)
        p = r.json()
        su_an = datetime.now().strftime("%H:%M:%S")
        msg = "".join([f"**{i}.** `ID: {x['id']}` - **{x['name']}**\n" for i, x in enumerate(p[:20], 1)])
        embed = discord.Embed(title="🚀 PROJECT GUN", color=0x2ecc71)
        embed.add_field(name="👥 Aktif", value=str(len(p)), inline=True)
        embed.add_field(name="🕒 Saat", value=su_an, inline=True)
        embed.add_field(name="📜 Liste", value=msg or "Boş", inline=False)
        await ctx.send(embed=embed)
    except: await ctx.send("⚠️ Sunucu kapalı!")

@bot.command()
async def clear(ctx, miktar: int = 10):
    if ctx.author.guild_permissions.manage_messages:
        await ctx.channel.purge(limit=miktar + 1)

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} AKTİF!')
    bot.add_view(TicketView())
    if not check_server_status.is_running(): check_server_status.start()
    await bot.change_presence(activity=discord.Streaming(name="!botyardım", url="https://twitch.tv/707"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
