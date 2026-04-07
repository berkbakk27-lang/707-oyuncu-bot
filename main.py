import discord
from discord.ext import commands
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime
import asyncio

# --- 7/24 AKTİF TUTMA (RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "707 Profesyonel Ticket Sistemi Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

TOKEN = os.getenv('PLAYER_BOT_TOKEN') 
FIVEM_IP = "185.211.100.221:30120"

# --- TICKET KAPATMA VE LOG KATEGORİSİNE TAŞIMA ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Bileti Kapat ve Arşivle', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='close_ticket_btn')
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        
        # "tickets log" Kategorisini bul veya oluştur
        log_category = discord.utils.get(guild.categories, name="tickets log")
        if not log_category:
            log_category = await guild.create_category("tickets log")

        old_channel_name = interaction.channel.name
        
        await interaction.response.send_message("🔒 Bilet kapatılıyor ve **tickets log** kategorisine taşınıyor...")
        await asyncio.sleep(2)

        # Kanalı log kategorisine taşı, ismini değiştir ve kullanıcı izinlerini al
        await interaction.channel.edit(category=log_category, name=f"log-{old_channel_name}")
        
        # İzinleri sıfırla (Sadece yetkililer görsün)
        await interaction.channel.set_permissions(guild.default_role, read_messages=False)
        for member in interaction.channel.members:
            if not member.guild_permissions.administrator:
                await interaction.channel.set_permissions(member, overwrite=None)

        # Log Mesajı
        embed = discord.Embed(title="💾 BİLET ARŞİVLENDİ", color=0xffa500, timestamp=datetime.now())
        embed.add_field(name="Kapatan Yetkili", value=interaction.user.mention)
        embed.add_field(name="Eski Kanal", value=old_channel_name)
        await interaction.channel.send(embed=embed)
        
        # Butonu mesajdan kaldır
        await interaction.edit_original_response(view=None)

# --- TICKET AÇMA MANTIĞI ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Destek Talebi Aç', style=discord.ButtonStyle.success, emoji='📩', custom_id='ticket_btn')
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # 1. KONTROL: Aktif bileti var mı? (Kanal isminden kontrol eder)
        ticket_channel_name = f"ticket-{user.name.lower()}".replace(" ", "-")
        existing_ticket = discord.utils.get(guild.text_channels, name=ticket_channel_name)
        
        if existing_ticket:
            return await interaction.response.send_message(f"❌ Kanka zaten açık bir biletin var: {existing_ticket.mention}\nOnu kapatmadan yenisini açamazsın!", ephemeral=True)

        # 2. KATEGORİ: "tickets" kategorisini bul/oluştur
        main_category = discord.utils.get(guild.categories, name="tickets")
        if not main_category:
            main_category = await guild.create_category("tickets")

        # 3. KANAL OLUŞTURMA
        channel = await guild.create_text_channel(
            name=ticket_channel_name,
            category=main_category
        )
        
        # İzinler (Kullanıcıya özel aç, @everyone'a kapat)
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(user, read_messages=True, send_messages=True, attach_files=True)

        await interaction.response.send_message(f"✅ Biletin oluşturuldu: {channel.mention}", ephemeral=True)
        
        # Bilet Kanalı İçeriği
        embed = discord.Embed(
            title="🎫 PROJECT GUN DESTEK", 
            description=f"Selam {user.mention},\n\nDestek ekibi kısa süre içinde burada olacak. Sorununu yazıp bekleyebilirsin.\n\n**Bilet Sahibi:** {user.name}\n**Durum:** Beklemede",
            color=0x3498db,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Bileti kapatmak için aşağıdaki butona basın.")
        
        await channel.send(content=f"{user.mention} | @everyone", embed=embed, view=CloseTicketView())

# --- KOMUTLAR ---

@bot.command()
@commands.has_permissions(administrator=True) # SADECE YÖNETİCİ
async def ticket(ctx):
    embed = discord.Embed(
        title="🎫 PROJECT GUN DESTEK HATTI", 
        description="Bir sorunun mu var? Veya şikayette mi bulunacaksın?\n\nAşağıdaki butona basarak yetkililerle görüşebilirsin.", 
        color=0x2ecc71
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def sunucu(ctx):
    try:
        r = requests.get(f"http://{FIVEM_IP}/players.json", timeout=5)
        p = r.json()
        embed = discord.Embed(title="🚀 PROJECT GUN DURUM", description=f"Şu an sunucuda **{len(p)}** kişi rol yapıyor!", color=0x2ecc71)
        await ctx.send(embed=embed)
    except:
        await ctx.send("⚠️ Sunucu verilerine şu an ulaşılamıyor!")

@bot.command()
async def clear(ctx, miktar: int = 10):
    if ctx.author.guild_permissions.manage_messages:
        await ctx.channel.purge(limit=miktar + 1)

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} BAŞLATILDI!')
    # Bot resleyince butonlar ölmesin diye:
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    await bot.change_presence(activity=discord.Streaming(name="!ticket", url="https://twitch.tv/707"))

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
