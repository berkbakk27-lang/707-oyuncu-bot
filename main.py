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
def home(): return "707 Loglu Sistem Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

TOKEN = os.getenv('PLAYER_BOT_TOKEN') 
FIVEM_IP = "185.211.100.221:30120"
LOG_KANAL_ID = 1491175628354097314 # Logların ve duyuruların gideceği kanal

# --- TICKET KAPATMA BUTONU ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Kanalı Kapat', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='close_ticket_btn')
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = bot.get_channel(LOG_KANAL_ID)
        if log_channel:
            embed = discord.Embed(title="🔒 BİLET KAPATILDI", color=0xff0000, timestamp=datetime.now())
            embed.add_field(name="Kapatan Yetkili", value=interaction.user.mention)
            embed.add_field(name="Kanal", value=interaction.channel.name)
            await log_channel.send(embed=embed)
        
        await interaction.response.send_message("🔒 Kanal 3 saniye içinde siliniyor...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

# --- TICKET AÇMA BUTONU ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Destek Talebi Aç', style=discord.ButtonStyle.success, emoji='📩', custom_id='ticket_btn')
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}")
        
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        # Log Gönder
        log_channel = bot.get_channel(LOG_KANAL_ID)
        if log_channel:
            log_embed = discord.Embed(title="📩 YENİ BİLET", color=0x2ecc71, timestamp=datetime.now())
            log_embed.add_field(name="Açan Kullanıcı", value=interaction.user.mention)
            log_embed.add_field(name="Kanal", value=channel.mention)
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message(f"✅ Biletin açıldı: {channel.mention}", ephemeral=True)
        
        # Bilet kanalına mesaj ve KAPAT butonu at
        embed = discord.Embed(title="👋 Hoş Geldin!", description="Sorununu buraya yazabilirsin. İşin bitince aşağıdaki butona basarak kapatabilirsin.", color=0x3498db)
        await channel.send(content=f"{interaction.user.mention} | @everyone", embed=embed, view=CloseTicketView())

# --- KOMUTLAR ---

@bot.command()
@commands.has_permissions(administrator=True) # SADECE YÖNETİCİ YAZABİLİR
async def ticket(ctx):
    embed = discord.Embed(title="🎫 DESTEK MERKEZİ", description="Bilet açmak için aşağıdaki butona tıkla.", color=0x3498db)
    await ctx.send(embed=embed, view=TicketView())

@ticket.error
async def ticket_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu sadece **Yöneticiler** kullanabilir kanka!", delete_after=5)

@bot.command()
async def botyardım(ctx):
    embed = discord.Embed(title="🤖 707 Komut Paneli", color=0xf1c40f)
    embed.add_field(name="🚀 Sunucu", value="`!sunucu`, `!oyuncusayi`", inline=False)
    embed.add_field(name="🎫 Destek", value="`!ticket` (Sadece Yönetici)", inline=False)
    embed.add_field(name="🛠️ Genel", value="`!clear`, `!steam`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def sunucu(ctx):
    try:
        r = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5)
        p = r.json()
        msg = "".join([f"**{i}.** `ID: {x['id']}` - **{x['name']}**\n" for i, x in enumerate(p[:20], 1)])
        embed = discord.Embed(title="🚀 PROJECT GUN", color=0x2ecc71, timestamp=datetime.now())
        embed.add_field(name="👥 Aktif", value=str(len(p)), inline=True)
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
    # Butonların bot kapanıp açılsa da çalışması için kayıt ediyoruz
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    await bot.change_presence(activity=discord.Streaming(name="!botyardım", url="https://twitch.tv/707"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
