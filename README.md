# Rhome Manager

Discord bot for publishing formatted Embed posts to the Rhome server from the bot's DMs.

Commands: /правило, /новости, /объявление, /видео, /стрим, /ивент, /помощь, /статус.

Publishing is restricted to the two configured Discord user IDs. The bot creates a new Embed post in the destination channel; it does not forward the DM.

## Discord setup
Enable Guild Install and User Install in the Developer Portal. Allow Guilds, Bot DMs and Private Channels contexts where available. Install the bot in Rhome with View Channels, Send Messages and Embed Links. Reset any token previously exposed and keep the new token private.

## Render environment
- DISCORD_TOKEN: newly reset bot token (secret)
- DISCORD_GUILD_ID: 1549682975443001415
- ALLOWED_USER_IDS: 1549414704248528946,1549531896411848717
- CHANNEL_RULES, CHANNEL_NEWS, CHANNEL_ANNOUNCEMENTS, CHANNEL_VIDEOS, CHANNEL_STREAMS, CHANNEL_EVENTS: destination channel IDs

Use Python, build command `pip install -r requirements.txt`, start command `python main.py`, Frankfurt region, Starter plan. Free instances sleep and are not suitable for reliable always-on Discord Gateway connections.
