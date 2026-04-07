import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime
import asyncio

# --- 7/24 AKTİF TUTMA (RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "707 Sistemi Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Render'daki Key ismi PLAYER_BOT_TOKEN olmalı
TOKEN = os.getenv('PLAYER_BOT_TOKEN') 
FIVEM_IP = "185.211.100.221:30120"
DUYURU_KANAL_ID = 1491175628354097314

last_status = None

# --- TICKET SİSTEMİ ALTYAPISI ---
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

# --- OTOMATİK DURUM DENETLEYİCİ ---
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
        if current_status == "online":
            embed = discord.Embed(title="✅ PROJECT GUN AKTİF", color=0x2ecc71, timestamp=datetime.now())
        else:
            embed = discord.Embed(title="❌ PROJECT GUN KAPALI", color=0xe74c3c, timestamp=datetime.now())
        await channel.send(embed=embed)
    last_status = current_status

# --- TÜM KOMUTLAR ---
@bot.command()
async def botyardım(ctx):
    embed = discord.Embed(title="🤖 707 Komut Paneli", color=0xf1c40f, timestamp=datetime.now())
    embed.add_field(name="🚀 Sunucu", value="`!sunucu` : Detaylı durum.\n`!oyuncusayi` : Sadece sayı.", inline=False)
    embed.add_field(name="🎫 Destek", value="`!ticket` : Butonu kurar.\n`!kapat` : Bileti siler.", inline=False)
    embed.add_field(name="🛠️ Genel", value="`!clear [sayı]` : Mesaj siler.\n`!steam [isim]` : Profil arar.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ticket(ctx):
    embed = discord.Embed(title="🎫 DESTEK SİSTEMİ", description="Bilet açmak için tıkla.", color=0x3498db)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def sunucu(ctx):
    try:
        r = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5)
        players = r.json()
        players.sort(key=lambda x: x['id'])
        msg = "".join([f"**{i}.** `ID: {p['id']}` - **{p['name']}**\n" for i, p in enumerate(players[:20], 1)])
        su_an = datetime.now().strftime("%H:%M:%S")
        embed = discord.Embed(title="🚀 PROJECT GUN DURUM", color=0x2ecc71, timestamp=datetime.now())
        embed.add_field(name="👥 Aktif", value=str(len(players)), inline=True)
        embed.add_field(name="🕒 Saat", value=su_an, inline=True)
        embed.add_field(name="📜 Oyuncular", value=msg or "Boş", inline=False)
        await ctx.send(embed=embed)
    except: await ctx.send("⚠️ Sunucuya ulaşılamadı!")

@bot.command()
async def oyuncusayi(ctx):
    try:
        r = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5)
        await ctx.send(f"🚀 **PROJECT GUN** | Şu an sunucuda **{len(r.json())}** kişi var.")
    except: await ctx.send("⚠️ Hata!")

@bot.command()
async def kapat(ctx):
    if "ticket-" in ctx.channel.name:
        await ctx.send("🔒 Kanal siliniyor...")
        await asyncio.sleep(2)
        await ctx.channel.delete()

@bot.command()
async def clear(ctx, miktar: int = 10):
    if ctx.author.guild_permissions.manage_messages:
        await ctx.channel.purge(limit=miktar + 1)
        await ctx.send(f"✅ {miktar} mesaj silindi.", delete_after=3)

@bot.command()
async def steam(ctx, *, isim: str):
    url = f"https://steamcommunity.com/search/users/#text={isim.replace(' ', '%20')}"
    await ctx.send(embed=discord.Embed(title=f"🔍 Steam: {isim}", description=f"[Profile Git]({url})", color=0x171a21))

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} AKTİF!')
    bot.add_view(TicketView())
    if not check_server_status.is_running(): check_server_status.start()
    await bot.change_presence(activity=discord.Streaming(name="!botyardım", url="https://twitch.tv/707"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
