"""
utils.py — shared helpers used across cogs.
"""

import re
import discord
from datetime import timedelta

ORDINALS = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]

def ordinal(n: int) -> str:
    """Return ordinal word for 1-10, or '11th' style after that."""
    if 1 <= n <= len(ORDINALS):
        return ORDINALS[n - 1]
    suffix = {1:"st",2:"nd",3:"rd"}.get(n % 10 if n % 100 not in (11,12,13) else 0, "th")
    return f"{n}{suffix}"

def parse_duration(text: str) -> timedelta | None:
    """
    Parse a human duration string like '1d 6h 30m 52s' into a timedelta.
    Returns None if unparseable.
    """
    pattern = re.compile(r"(\d+)\s*([dhms])", re.IGNORECASE)
    matches = pattern.findall(text)
    if not matches:
        return None
    total = timedelta()
    for value, unit in matches:
        value = int(value)
        unit = unit.lower()
        if unit == "d":
            total += timedelta(days=value)
        elif unit == "h":
            total += timedelta(hours=value)
        elif unit == "m":
            total += timedelta(minutes=value)
        elif unit == "s":
            total += timedelta(seconds=value)
    return total if total.total_seconds() > 0 else None

def format_duration(td: timedelta) -> str:
    """Format a timedelta as e.g. '1d 6h 30min 52sec'."""
    total = int(td.total_seconds())
    d, remainder = divmod(total, 86400)
    h, remainder = divmod(remainder, 3600)
    m, s = divmod(remainder, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}min")
    if s: parts.append(f"{s}sec")
    return " ".join(parts) or "0sec"

def mod_embed(color: discord.Color, title: str, **fields) -> discord.Embed:
    """Create a clean moderation embed."""
    embed = discord.Embed(title=title, color=color)
    for name, value in fields.items():
        embed.add_field(name=name.replace("_", " ").title(), value=value, inline=True)
    return embed

async def log_action(bot, guild: discord.Guild, embed: discord.Embed):
    """Send an embed to the configured log channel, if any."""
    from database import get_setting
    log_id = await get_setting(guild.id, "log_channel")
    if not log_id:
        return
    channel = guild.get_channel(int(log_id))
    if channel:
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
