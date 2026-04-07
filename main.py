
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
def home(): return "707 Birleşik Sistem Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Render'daki Environment Variables kısmında bu isimle (PLAYER_BOT_TOKEN) kayıtlı kalsın
TOKEN = os.getenv('PLAYER_BOT_TOKEN') 
FIVEM_IP = "185.211.100.221:30120"
# Sunucu açıldı/kapandı bilgisinin gideceği kanal ID'si
DUYURU_KANAL_ID = 1491175628354097314

last_status = None

# --- TICKET GÖRÜNÜMÜ ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Destek Talebi Aç', style=discord.ButtonStyle.success, emoji='📩', custom_id='ticket_btn')
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        # Bilet kanalı oluştur
        channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}")
        
        # Yetkileri ayarla
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        await interaction.response.send_message(f"✅ Biletin açıldı: {channel.mention}", ephemeral=True)
        await channel.send(f"👋 {interaction.user.mention} Hoş geldin! Yetkililer gelene kadar sorununu yazabilirsin.\n\nKapatmak için: `!kapat` yazabilirsin.")

# --- OTOMATİK DURUM DENETLEYİCİ (60 Saniyede Bir) ---
@tasks.loop(seconds=60)
async def check_server_status():
    global last_status
    channel = bot.get_channel(DUYURU_KANAL_ID)
    if not channel: return

    try:
        r = requests.get(f"http://{FIVEM_IP}/info.json", timeout=5)
        current_status = "online" if r.status_code == 200 else "offline"
    except:
        current_status = "offline"

    if last_status is not None and current_status != last_status:
        if current_status == "online":
            embed = discord.Embed(title="✅ PROJECT GUN AKTİF", description="Sunucu şu an açık! Giriş yapabilirsiniz.", color=0x2ecc71, timestamp=datetime.now())
        else:
            embed = discord.Embed(title="❌ PROJECT GUN KAPALI", description="Sunucu bağlantısı kesildi veya bakıma girildi.", color=0xe74c3c, timestamp=datetime.now())
        await channel.send(embed=embed)
    
    last_status = current_status

# --- KOMUTLAR ---

@bot.command()
async def botyardım(ctx):
    embed = discord.Embed(title="🤖 707 Bot Komut Paneli", color=discord.Color.gold(), timestamp=datetime.now())
    embed.add_field(name="🚀 Sunucu", value="`!sunucu` : Detaylı durum ve ilk 20 oyuncu.\n`!oyuncusayi` : Sadece aktif kişi sayısı.", inline=False)
    embed.add_field(name="🎫 Destek", value="`!ticket` : Destek butonu oluşturur.\n`!kapat` : Bilet kanalını siler.", inline=False)
    embed.add_field(name="🛠️ Diğer", value="`!clear [sayı]` : Mesaj temizler.\n`!steam [isim]` : Profil arar.", inline=False)
    embed.set_footer(text=f"Sorgulayan: {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command()
async def ticket(ctx):
    embed = discord.Embed(title="🎫 DESTEK MERKEZİ", description="Yetkililerle iletişime geçmek için butona tıklayın.", color=0x3498db)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def sunucu(ctx):
    try:
        r = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5)
        players = r.json()
        count = len(players)
        players.sort(key=lambda x: x['id'])
        
        msg = "".join([f"**{i}.** `ID: {p['id']}` - **{p['name']}**\n" for i, p in enumerate(players[:20], 1)])
        
        embed = discord.Embed(title="🚀 PROJECT GUN DURUM", color=0x2ecc71, timestamp=datetime.now())
        embed.add_field(name="👥 Aktif Oyuncu", value=str(count), inline=True)
        embed.add_field(name="📜 Oyuncu Listesi (İlk 20)", value=msg or "Sunucu boş.", inline=False)
        await ctx.send(embed=embed)
    except:
        await ctx.send("⚠️ Sunucu verilerine ulaşılamadı!")

@bot.command()
async def kapat(ctx):
    if "ticket-" in ctx.channel.name:
        await ctx.send("🔒 Kanal 3 saniye içinde kalıcı olarak siliniyor...")
        await asyncio.sleep(3)
        await ctx.channel.delete()

@bot.command()
async def clear(ctx, miktar: int = 10):
    if ctx.author.guild_permissions.manage_messages:
        await ctx.channel.purge(limit=miktar + 1)
        await ctx.send(f"✅ {miktar} mesaj temizlendi.", delete_after=3)

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} Birleşik Sistem Aktif!')
    bot.add_view(TicketView()) # Butonların kalıcı olması için
    if not check_server_status.is_running():
        check_server_status.start()
    await bot.change_presence(activity=discord.Streaming(name="!botyardım", url="https://twitch.tv/707"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
