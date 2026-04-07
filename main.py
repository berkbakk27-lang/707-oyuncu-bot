import discord
from discord.ext import commands
import requests
import os
from flask import Flask
from threading import Thread

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Oyuncu Botu Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('PLAYER_BOT_TOKEN') # Render'da bu isimle kaydet
FIVEM_IP = "185.211.100.221:30120" 

@bot.command()
async def oyuncusayi(ctx):
    try:
        url = f"http://{FIVEM_IP}/players.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            count = len(response.json())
            embed = discord.Embed(description=f"🎮 **PROJECT GUN** | Aktif Oyuncu: **{count}**", color=0x2ecc71)
            await ctx.send(embed=embed)
    except:
        await ctx.send("⚠️ Sunucuya bağlanılamadı.")

@bot.command()
async def oyuncu(ctx):
    try:
        url = f"http://{FIVEM_IP}/players.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            players = response.json()
            count = len(players)
            if count == 0: return await ctx.send("🌵 Sunucu şu an boş.")

            players.sort(key=lambda x: x['id']) # ID'ye göre sırala

            player_data = ""
            for i, p in enumerate(players[:20], 1):
                player_data += f"**{i}.** `ID: {p['id']}` - **{p['name']}**\n"
            
            if count > 20:
                player_data += f"\n*...ve {count - 20} kişi daha aktif.*"

            embed = discord.Embed(title="🛰️ PROJECT GUN Sıralı Liste", description=player_data, color=0x3498db)
            embed.set_footer(text=f"707 Oyuncu Botu | Toplam: {count}")
            await ctx.send(embed=embed)
    except:
        await ctx.send("⚠️ Bağlantı hatası!")

@bot.event
async def on_ready():
    # Botun durumunda kaç kişi olduğunu gösterelim
    print(f'{bot.user.name} Sunucu Takibi İçin Hazır!')
    await bot.change_presence(activity=discord.Game(name="Project Gun Player Tracker"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
