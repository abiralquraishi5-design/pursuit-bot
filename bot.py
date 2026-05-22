"""
bot.py — Entry point for the all-in-one Discord bot.

Supports both prefix commands (! and ?) and slash commands.
"""

import discord
from discord.ext import commands, tasks
import os, asyncio
from dotenv import load_dotenv
from database import init_db, get_setting, get_expired_tempbans, remove_tempban
from datetime import datetime, timezone

load_dotenv()

# ── Dynamic prefix: supports ! and ? always; per-guild prefix from DB ──────────
async def get_prefix(bot, message):
    prefixes = ["!", "?"]
    if message.guild:
        custom = await get_setting(message.guild.id, "prefix")
        if custom and custom not in prefixes:
            prefixes.append(custom)
    return commands.when_mentioned_or(*prefixes)(bot, message)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

COGS = [
    "cogs.moderation",
    "cogs.utility",
    "cogs.reaction_roles",
    "cogs.verification",
    "cogs.leveling",
    "cogs.fun",
    "cogs.ai",
    "cogs.settings",
    "cogs.help",
]

# ── Events ─────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()
    print("✅ Slash commands synced globally.")
    check_tempbans.start()

@bot.event
async def on_guild_join(guild):
    # Ensure guild has a default settings row
    await get_setting(guild.id, "prefix")

@bot.event
async def on_member_join(member):
    from database import get_auto_roles, get_setting as gs
    # Auto-roles
    role_ids = await get_auto_roles(member.guild.id)
    for rid in role_ids:
        role = member.guild.get_role(int(rid))
        if role:
            try:
                await member.add_roles(role, reason="Auto-role on join")
            except discord.Forbidden:
                pass
    # Welcome message
    ch_id = await gs(member.guild.id, "welcome_channel")
    msg   = await gs(member.guild.id, "welcome_message")
    if ch_id and msg:
        ch = member.guild.get_channel(int(ch_id))
        if ch:
            welcome = msg.replace("{user}", member.mention) \
                        .replace("{server}", member.guild.name) \
                        .replace("{count}", str(member.guild.member_count))
            try:
                await ch.send(welcome)
            except discord.Forbidden:
                pass

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing: `{error.param.name}`. Use `!help` or `/help`.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Bad argument: {error}")
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ I don't have the required permissions for that.")
    else:
        await ctx.send(f"❌ Error: {error}")
        raise error

# ── Background task: unban temp-banned users ───────────────────────────────────
@tasks.loop(seconds=30)
async def check_tempbans():
    now = datetime.now(timezone.utc)
    expired = await get_expired_tempbans(now)
    for guild_id, user_id in expired:
        guild = bot.get_guild(int(guild_id))
        if guild:
            try:
                user = await bot.fetch_user(int(user_id))
                await guild.unban(user, reason="Temp-ban expired")
            except Exception:
                pass
        await remove_tempban(guild_id, user_id)

# ── Startup ────────────────────────────────────────────────────────────────────
async def main():
    async with bot:
        await init_db()
        print("✅ Database initialised.")
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
