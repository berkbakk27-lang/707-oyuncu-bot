import discord
from discord.ext import commands
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime
import asyncio

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Sistem Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

TOKEN = os.getenv('PLAYER_BOT_TOKEN') 
FIVEM_IP = "185.211.100.221:30120"

# --- TICKET KAPATMA ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Başvuruyu Kapat ve Arşivle', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='close_ticket_btn')
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        log_cat = discord.utils.get(guild.categories, name="tickets log") or await guild.create_category("tickets log")
        
        await interaction.response.send_message("🔒 Başvuru arşivleniyor...")
        await asyncio.sleep(2)

        await interaction.channel.edit(category=log_cat, name=f"arsiv-{interaction.channel.name}")
        await interaction.channel.set_permissions(guild.default_role, read_messages=False)
        for m in interaction.channel.members:
            if not m.guild_permissions.administrator:
                await interaction.channel.set_permissions(m, overwrite=None)

        await interaction.channel.send(embed=discord.Embed(title="💾 ARŞİVLENDİ", description=f"Kapatan: {interaction.user.mention}", color=0xffa500))
        await interaction.edit_original_response(view=None)

# --- TICKET AÇMA ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='707 Fam Başvurusu Yap', style=discord.ButtonStyle.success, emoji='📝', custom_id='ticket_btn')
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        ticket_name = f"707-fam-{user.name.lower()}".replace(" ", "-")

        if discord.utils.get(guild.text_channels, name=ticket_name):
            return await interaction.response.send_message("❌ Zaten açık bir başvurun var!", ephemeral=True)

        main_cat = discord.utils.get(guild.categories, name="tickets") or await guild.create_category("tickets")
        channel = await guild.create_text_channel(name=ticket_name, category=main_cat)
        
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(user, read_messages=True, send_messages=True)

        await interaction.response.send_message(f"✅ Kanal açıldı: {channel.mention}", ephemeral=True)
        
        embed = discord.Embed(title="🦅 707 FAM BAŞVURU", description=f"Hoş geldin {user.mention}!\n\nLütfen İsim, Yaş ve Günlük Aktiflik süreni yaz.\nYetkililer birazdan burada olacak.", color=0x2ecc71)
        await channel.send(content=f"{user.mention} | @everyone", embed=embed, view=CloseTicketView())

# --- KOMUTLAR ---
@bot.command()
async def botyardım(ctx):
    embed = discord.Embed(title="🤖 707 Sistem Menüsü", color=0xf1c40f)
    embed.add_field(name="🚀 Sunucu", value="`!sunucu`, `!oyuncusayi`", inline=False)
    embed.add_field(name="🦅 Aile", value="`!ticket` (Başvuru Butonunu Atar)", inline=False)
    embed.add_field(name="🛠️ Diğer", value="`!clear`, `!steam`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def ticket(ctx):
    embed = discord.Embed(title="🦅 707 FAM BAŞVURU", description="Aileye katılmak için butona bas!", color=0x2ecc71)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def sunucu(ctx):
    try:
        r = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5).json()
        await ctx.send(embed=discord.Embed(title="🚀 PROJECT GUN", description=f"Aktif Oyuncu: **{len(r)}**", color=0x2ecc71))
    except: await ctx.send("⚠️ Sunucu kapalı!")

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} AKTİF!')
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    # BURASI DÜZELDİ: Artık botun üstünde !botyardım yazacak
    await bot.change_presence(activity=discord.Streaming(name="!botyardım", url="https://twitch.tv/707"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
