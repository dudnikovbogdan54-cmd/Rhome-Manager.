import os
import logging
import asyncio
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("rhome-manager")

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "1549682975443001415"))
ALLOWED_USERS = {
    int(value.strip())
    for value in os.getenv("ALLOWED_USER_IDS", "1549414704248528946,1549531896411848717").split(",")
    if value.strip().isdigit()
}
CHANNELS = {
    "rules": ("CHANNEL_RULES", "Правила"),
    "news": ("CHANNEL_NEWS", "Новости"),
    "announcements": ("CHANNEL_ANNOUNCEMENTS", "Объявления"),
    "videos": ("CHANNEL_VIDEOS", "Новые видео"),
    "streams": ("CHANNEL_STREAMS", "Стримы"),
    "events": ("CHANNEL_EVENTS", "Мероприятия"),
}
if not TOKEN:
    raise RuntimeError("Не задана переменная окружения DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

async def private_denial(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("У тебя нет доступа к управлению публикациями Rhome Manager.", ephemeral=True)

async def publish(interaction: discord.Interaction, key: str, title: str, text: str, color: discord.Color) -> None:
    if not is_allowed(interaction.user.id):
        await private_denial(interaction)
        return
    if interaction.guild is not None:
        await interaction.response.send_message("Эту команду нужно использовать в личных сообщениях с ботом.", ephemeral=True)
        return
    env_name, display_name = CHANNELS[key]
    raw_channel_id = os.getenv(env_name, "").strip()
    if not raw_channel_id.isdigit():
        await interaction.response.send_message(f"Канал «{display_name}» ещё не настроен. Добавь ID в Render → Environment → {env_name}.", ephemeral=True)
        return
    channel_id = int(raw_channel_id)
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            channel = None
    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        await interaction.response.send_message(f"Не удалось найти текстовый канал «{display_name}». Проверь ID и права бота.", ephemeral=True)
        return
    if channel.guild.id != GUILD_ID:
        await interaction.response.send_message("Этот канал не относится к настроенному серверу Rhome.", ephemeral=True)
        return
    clean_text = text.strip()
    if not clean_text or len(clean_text) > 4000:
        await interaction.response.send_message("Текст должен содержать от 1 до 4000 символов.", ephemeral=True)
        return
    embed = discord.Embed(title=title, description=clean_text, color=color, timestamp=datetime.now(timezone.utc))
    embed.set_footer(text="Rhome • Официальная публикация")
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("У бота нет прав отправлять сообщения или Embed-сообщения в этом канале.", ephemeral=True)
        return
    except discord.HTTPException:
        await interaction.response.send_message("Discord не принял публикацию. Попробуй ещё раз позже.", ephemeral=True)
        return
    await interaction.response.send_message(f"Опубликовано в канале «{display_name}».", ephemeral=True)
    log.info("Published %s by user %s to channel %s", key, interaction.user.id, channel_id)

def command_contexts():
    return app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)

def command_installs():
    return app_commands.allowed_installs(guilds=True, users=True)

@bot.event
async def on_ready():
    log.info("Connected as %s (%s)", bot.user, bot.user.id if bot.user else "?")
    try:
        synced = await bot.tree.sync()
        log.info("Synced %d global application commands", len(synced))
    except Exception:
        log.exception("Command sync failed")

@bot.tree.command(name="rule", description="Опубликовать правило на сервере Rhome", name_localizations={"ru": "правило"})
@app_commands.describe(text="Текст правила")
@command_contexts()
@command_installs()
async def rule(interaction: discord.Interaction, text: str):
    await publish(interaction, "rules", "ПРАВИЛА СЕРВЕРА", text, discord.Color.from_rgb(45, 125, 235))

@bot.tree.command(name="news", description="Опубликовать новость", name_localizations={"ru": "новости"})
@app_commands.describe(text="Текст новости")
@command_contexts()
@command_installs()
async def news(interaction: discord.Interaction, text: str):
    await publish(interaction, "news", "НОВОСТИ RHOME", text, discord.Color.from_rgb(35, 150, 220))

@bot.tree.command(name="announcement", description="Опубликовать объявление", name_localizations={"ru": "объявление"})
@app_commands.describe(text="Текст объявления")
@command_contexts()
@command_installs()
async def announcement(interaction: discord.Interaction, text: str):
    await publish(interaction, "announcements", "ОБЪЯВЛЕНИЕ", text, discord.Color.from_rgb(75, 105, 220))

@bot.tree.command(name="video", description="Сообщить о новом видео", name_localizations={"ru": "видео"})
@app_commands.describe(text="Название, описание и ссылка на видео")
@command_contexts()
@command_installs()
async def video(interaction: discord.Interaction, text: str):
    await publish(interaction, "videos", "ВЫШЛО НОВОЕ ВИДЕО", text, discord.Color.from_rgb(225, 65, 65))

@bot.tree.command(name="stream", description="Опубликовать анонс стрима", name_localizations={"ru": "стрим"})
@app_commands.describe(text="Время, тема и ссылка на стрим")
@command_contexts()
@command_installs()
async def stream(interaction: discord.Interaction, text: str):
    await publish(interaction, "streams", "СКОРО СТРИМ", text, discord.Color.from_rgb(145, 85, 220))

@bot.tree.command(name="event", description="Опубликовать мероприятие", name_localizations={"ru": "ивент"})
@app_commands.describe(text="Описание, дата и условия участия")
@command_contexts()
@command_installs()
async def event(interaction: discord.Interaction, text: str):
    await publish(interaction, "events", "МЕРОПРИЯТИЕ RHOME", text, discord.Color.from_rgb(35, 175, 135))

@bot.tree.command(name="help", description="Показать список команд", name_localizations={"ru": "помощь"})
@command_contexts()
@command_installs()
async def help_command(interaction: discord.Interaction):
    if not is_allowed(interaction.user.id):
        await private_denial(interaction)
        return
    embed = discord.Embed(title="RHOME MANAGER", description="\n".join([
        "`/правило` — публикация правила", "`/новости` — публикация новости",
        "`/объявление` — объявление", "`/видео` — анонс нового видео",
        "`/стрим` — анонс стрима", "`/ивент` — мероприятие", "`/статус` — состояние бота"
    ]), color=discord.Color.from_rgb(45, 125, 235))
    embed.set_footer(text="Команды доступны только двум администраторам")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="Проверить состояние бота", name_localizations={"ru": "статус"})
@command_contexts()
@command_installs()
async def status(interaction: discord.Interaction):
    if not is_allowed(interaction.user.id):
        await private_denial(interaction)
        return
    embed = discord.Embed(title="СТАТУС RHOME MANAGER", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Подключение", value="Онлайн", inline=True)
    embed.add_field(name="Задержка", value=f"{round(bot.latency * 1000)} мс", inline=True)
    embed.add_field(name="Сервер", value=str(GUILD_ID), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def health(_request):
    return web.json_response({"ok": True, "service": "Rhome Manager"})

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "10000")))
    await site.start()
    log.info("Health server started")

async def main():
    await start_health_server()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
