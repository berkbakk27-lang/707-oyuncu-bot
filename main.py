import discord
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Gelişmiş Sunucu Botu Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

TOKEN = os.getenv('PLAYER_BOT_TOKEN')
FIVEM_IP = "185.211.100.221:30120"
DUYURU_KANAL_ID = 1491175628354097314 # Senin verdiğin kanal ID'si

last_status = None 

# --- OTOMATİK DURUM DENETLEYİCİ (60 Saniyede Bir) ---
@tasks.loop(seconds=60)
async def check_server_status():
    global last_status
    channel = bot.get_channel(DUYURU_KANAL_ID)
    if not channel: return

    try:
        # Sunucu bilgilerini kontrol et
        response = requests.get(f"http://{FIVEM_IP}/info.json", timeout=5)
        current_status = "online" if response.status_code == 200 else "offline"
    except:
        current_status = "offline"

    # Durum değişikliği varsa duyuru yap
    if last_status is not None and current_status != last_status:
        if current_status == "online":
            embed = discord.Embed(
                title="✅ PROJECT GUN ÇEVRİMİÇİ",
                description="Sunucu şu an aktif! Giriş yapabilirsiniz.",
                color=0x2ecc71,
                timestamp=datetime.now()
            )
        else:
            embed = discord.Embed(
                title="❌ PROJECT GUN ÇEVRİMDIŞI",
                description="Sunucu bağlantısı kesildi veya bakıma girildi.",
                color=0xe74c3c,
                timestamp=datetime.now()
            )
        await channel.send(embed=embed)
    
    last_status = current_status

# --- KOMUT: !sunucu (HEPSİ BİR ARADA) ---
@bot.command()
async def sunucu(ctx):
    try:
        # Oyuncu ve Sunucu verilerini çek
        p_res = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5)
        
        if p_res.status_code == 200:
            players = p_res.json()
            count = len(players)
            players.sort(key=lambda x: x['id']) # ID Sıralama

            # Saat Bilgisi
            su an = datetime.now().strftime("%H:%M:%S")

            # İlk 20 Oyuncu Listesi
            player_list = ""
            for i, p in enumerate(players[:20], 1):
                player_list += f"**{i}.** `ID: {p['id']}` - **{p['name']}**\n"
            
            if not player_list: player_list = "Sunucuda kimse yok."
            if count > 20: player_list += f"\n*...ve {count-20} kişi daha aktif.*"

            embed = discord.Embed(
                title="🚀 PROJECT GUN SUNUCU DURUMU",
                color=0x3498db,
                timestamp=datetime.now()
            )
            embed.add_field(name="🌐 Sunucu IP", value=f"`{FIVEM_IP}`", inline=True)
            embed.add_field(name="👥 Aktif Oyuncu", value=f"**{count}**", inline=True)
            embed.add_field(name="🕒 Güncel Saat", value=f"`{su an}`", inline=True)
            embed.add_field(name="📜 Oyuncu Listesi (İlk 20)", value=player_list, inline=False)
            
            embed.set_footer(text="707 Oyuncu Botu | Sistem Hazır")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Sunucu verileri şu an alınamıyor.")
    except:
        await ctx.send("⚠️ Sunucuya bağlanılamadı. IP veya Port kapalı olabilir.")

# --- DİĞER KOMUTLAR ---
@bot.command()
async def yardım(ctx):
    embed = discord.Embed(title="📜 707 Bot Komutları", color=discord.Color.gold())
    embed.add_field(name="!sunucu", value="Tüm sunucu bilgilerini ve oyuncuları gösterir.", inline=False)
    embed.add_field(name="!steam [isim]", value="Kullanıcı adıyla Steam profili arar.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def steam(ctx, *, isim: str):
    search_url = f"https://steamcommunity.com/search/users/#text={isim.replace(' ', '%20')}"
    embed = discord.Embed(title=f"🔍 Steam Arama: {isim}", description=f"[Buraya Tıkla]({search_url})", color=0x171a21)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user.name} Project Gun için her şeye hazır!')
    check_server_status.start() # 60 saniyelik döngüyü başlat
    await bot.change_presence(activity=discord.Game(name="!sunucu | Project Gun"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
