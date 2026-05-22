"""
cogs/leveling.py
XP and leveling system — replaces MEE6 / Arcane.
"""

import discord
from discord.ext import commands
import random
from database import add_xp, get_level_data, set_level, get_leaderboard

XP_PER_MESSAGE = (15, 25)          # random XP range per message
XP_COOLDOWN_SECONDS = 60           # seconds between XP gains per user
XP_FOR_LEVEL = lambda lvl: 5 * (lvl ** 2) + 50 * lvl + 100   # MEE6-style formula

class Leveling(commands.Cog):
    """⭐ Leveling — earn XP by chatting."""

    def __init__(self, bot):
        self.bot = bot
        self._cooldowns: dict[tuple, float] = {}  # (guild_id, user_id) -> last_xp_time

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        import time
        key = (message.guild.id, message.author.id)
        now = time.time()
        if now - self._cooldowns.get(key, 0) < XP_COOLDOWN_SECONDS:
            return
        self._cooldowns[key] = now

        xp_gain = random.randint(*XP_PER_MESSAGE)
        await add_xp(message.guild.id, message.author.id, xp_gain)
        xp, level = await get_level_data(message.guild.id, message.author.id)
        xp_needed = XP_FOR_LEVEL(level + 1)

        if xp >= xp_needed:
            new_level = level + 1
            await set_level(message.guild.id, message.author.id, xp, new_level)
            await message.channel.send(
                f"🎉 {message.author.mention} leveled up to **Level {new_level}**! 🚀"
            )

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        """Check your rank. Usage: !rank [@user]"""
        m = member or ctx.author
        xp, level = await get_level_data(ctx.guild.id, m.id)
        xp_needed = XP_FOR_LEVEL(level + 1)
        bar_filled = int((xp / xp_needed) * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        embed = discord.Embed(title=f"⭐ {m.display_name}'s Rank", color=m.color)
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp} / {xp_needed}", inline=True)
        embed.add_field(name="Progress", value=f"`[{bar}]`", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx):
        """Show the XP leaderboard. Usage: !leaderboard"""
        entries = await get_leaderboard(ctx.guild.id, limit=10)
        if not entries:
            return await ctx.send("📭 No XP data yet. Start chatting!")
        embed = discord.Embed(title=f"🏆 {ctx.guild.name} Leaderboard", color=discord.Color.gold())
        medals = ["🥇","🥈","🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        lines = []
        for i, (user_id, xp, level) in enumerate(entries):
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"Unknown ({user_id})"
            lines.append(f"{medals[i]} **{name}** — Level {level} | {xp} XP")
        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

    @commands.command(name="givexp")
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx, member: discord.Member, amount: int):
        """Give XP to a member. Usage: !givexp @user 500"""
        await add_xp(ctx.guild.id, member.id, amount)
        await ctx.send(f"✅ Gave **{amount} XP** to **{member.display_name}**.")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
